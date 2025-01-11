from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, Union
from threading import Lock
from functools import reduce
from dataclasses import dataclass
import logging

import numpy as np
from numpy.typing import NDArray
from pydispatch import dispatcher

from src.openadr_node.database.loadprofile_manager import LoadProfileManager
from src.openadr_node.load_distribution_calculator import NodeResourceCalculator
from src.openadr_node.models.event import ResourceConsumption

# Configure logging
logger = logging.getLogger(__name__)


class NodeControllerError(Exception):
  """Base exception class for NodeResourceController errors."""

  pass


class LoadProfileError(NodeControllerError):
  """Raised when there's an error updating or processing load profiles."""

  pass


class ConsumptionError(NodeControllerError):
  """Raised when there's an error processing consumption data."""

  pass


@dataclass
class VENState:
  """Data class representing VEN state information."""

  resource_data: Dict[str, float]
  last_updated: datetime
  status: str


class NodeResourceController:
  """
  Controller for managing Virtual End Node (VEN) resources and load distribution.

  This class coordinates updates between VENs and delegates complex calculations
  to NodeResourceCalculator. It manages VEN states, consumption data, and load
  profile updates while maintaining thread safety.

  Attributes:
      _ven_data: Mapping of VEN IDs to their resource consumption data
      _current_consumption: Current total consumption across all VENs
      _pending_vens: Set of VENs waiting to be activated
      _active_vens: Set of currently active VENs
  """

  # Constants
  TIMESTAMP_MULTIPLIER: int = 1000  # Convert seconds to milliseconds
  DISPATCHER_SENDER: str = 'nm'

  def __init__(self, load_profile_manager: LoadProfileManager):
    """
    Initialize the NodeResourceController.

    Args:
        load_profile_manager: Manager instance for handling load profiles
    """
    self._load_profile_manager = load_profile_manager
    self._calculator = NodeResourceCalculator(load_profile_manager)
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._current_consumption: float = 0.0
    self._lock = Lock()
    self._pending_vens: Set[str] = set()
    self._active_vens: Set[str] = set()

  def _validate_ven_id(self, ven_id: str) -> None:
    """
    Validate VEN ID format and uniqueness.

    Args:
        ven_id: VEN identifier to validate

    Raises:
        ValueError: If VEN ID is invalid
    """
    if not isinstance(ven_id, str) or not ven_id:
      raise ValueError('VEN ID must be a non-empty string')

    if ven_id in self._active_vens:
      raise ValueError(f'VEN {ven_id} is already active')

  def on_register_report(self, ven_id: str) -> None:
    """
    Register a new VEN to the pending queue.

    Args:
        ven_id: Unique identifier for the VEN

    Raises:
        ValueError: If VEN ID is invalid
    """
    try:
      self._validate_ven_id(ven_id)
      self._pending_vens.add(ven_id)
      logger.info(
        f'Added VEN {ven_id} to pending queue. Current pending VENs: {self._pending_vens}'
      )
    except ValueError as e:
      logger.error(f'Failed to register VEN: {str(e)}')
      raise

  def _transform_load_profile(self, df: Any) -> List[Dict[str, Union[int, float]]]:
    """
    Transform load profile data from database format.

    Args:
        df: Database load profile data

    Returns:
        List of transformed load profile entries
    """
    return [
      {
        'dstart': int(df['dstart'][i]),
        'duration': int(df['duration'][i]),
        'signal_payload': float(df['signal_payload'][i]),
      }
      for i in range(len(df['dstart']))
    ]

  def _process_z_values(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    current_allowed_consumption: Dict[str, Any],
    use_z_directly: bool,
  ) -> NDArray[np.float64]:
    """
    Process and calculate Z values for load distribution.

    Args:
        ven_ids: Array of VEN identifiers
        consumption_values: Array of consumption values
        current_allowed_consumption: Current consumption limits
        use_z_directly: Flag to bypass stored z-values

    Returns:
        Array of calculated Z values
    """
    if len(ven_ids) > 0 and not use_z_directly:
      latest_z_values = self._load_profile_manager.get_latest_z_values()
      processed_z_values = self._calculator.process_latest_z_values(
        latest_z_values, ven_ids
      )

      if processed_z_values is not None:
        self._calculator._z = processed_z_values
        _, z_neu = self._calculator.calculate_load_distribution(
          ven_ids, consumption_values, current_allowed_consumption['signal_payload']
        )
        return z_neu

    z_value = self._calculator.calculate_z_value(
      current_allowed_consumption, len(self._active_vens), len(self._pending_vens)
    )
    self._calculator._z = z_value
    return np.full_like(consumption_values, z_value)

  def update_load_profile(
    self,
    sender: str,
    data: Optional[List[Dict[str, Any]]],
    use_z_directly: bool = False,
  ) -> None:
    """
    Update load profiles and recalculate resource distribution.

    Args:
        sender: Identity of the update sender
        data: Load profile data to update
        use_z_directly: Flag to use direct z-value calculation

    Raises:
        LoadProfileError: If the update process fails
    """
    try:
      processed_data = (
        data
        if data is not None
        else self._transform_load_profile(self._load_profile_manager.get_load_profile())
      )

      if not all(
        map(
          lambda x: all(k in x for k in ['dstart', 'duration', 'signal_payload']),
          processed_data,
        )
      ):
        processed_data = self._calculator.process_load_profile_data(processed_data)

      self._load_profile_manager.insert_load_profile(processed_data)
      current_timestamp = int(
        datetime.now(timezone.utc).timestamp() * self.TIMESTAMP_MULTIPLIER
      )

      current_allowed_consumption, current_consumption = (
        self._calculator.get_current_data(current_timestamp)
      )

      if not current_allowed_consumption:
        raise LoadProfileError('No current_allowed_consumption available.')

      ven_ids, consumption_values = self._calculator.prepare_consumption_array(
        current_consumption
      )

      z_neu = self._process_z_values(
        ven_ids, consumption_values, current_allowed_consumption, use_z_directly
      )

      if len(ven_ids) > 0:
        self._load_profile_manager.insert_z_values(ven_ids, z_neu, current_timestamp)
        intervals = self._calculator.generate_time_intervals()
        new_data_structure = self._calculator.create_ven_profiles(
          ven_ids, z_neu, intervals
        )
        dispatcher.send(
          sender=self.DISPATCHER_SENDER,
          signal='update_load_profile',
          data=new_data_structure,
        )

    except Exception as e:
      logger.error(f'Error calculating load distribution: {str(e)}')
      raise LoadProfileError(f'Failed to update load profile: {str(e)}') from e

  def _calculate_total_consumption(self) -> float:
    """
    Calculate total consumption across all VENs.

    Returns:
        Total consumption value
    """
    return reduce(lambda acc, d: acc + sum(d.values()), self._ven_data.values(), 0.0)

  def _handle_ven_activation(self, ven_id: str) -> None:
    """
    Handle the activation of a pending VEN.

    Args:
        ven_id: Identifier of the VEN to activate
    """
    if ven_id in self._pending_vens:
      self._pending_vens.remove(ven_id)
      self._active_vens.add(ven_id)
      logger.info(
        f'VEN {ven_id} moved from pending to active. Triggering recalculation.'
      )
      self._calculator._z = None
      self.update_load_profile(None, None, use_z_directly=True)

  def update_consumption_data(self, sender: str, data: ResourceConsumption) -> None:
    """
    Update consumption data and manage VEN state changes.

    Args:
        sender: Identity of the update sender
        data: Resource consumption data

    Raises:
        ConsumptionError: If the update process fails
    """
    try:
      with self._lock:
        ven_data = self._ven_data.setdefault(data.ven_id, {})
        ven_data[data.resource_id] = data.data[1]
        self._current_consumption = self._calculate_total_consumption()

        consumption_data = {
          'timestamp': int(
            datetime.now(timezone.utc).timestamp() * self.TIMESTAMP_MULTIPLIER
          ),
          'ven_id': data.ven_id,
          'resource_id': data.resource_id,
          'value': data.data[1],
        }

        self._load_profile_manager.insert_consumption(consumption_data)
        self._handle_ven_activation(data.ven_id)

        logger.debug(f'Updated consumption data - Total: {self._current_consumption}')
        dispatcher.send(
          sender=self.DISPATCHER_SENDER,
          signal='update_consumption_data',
          data=self._current_consumption,
        )

    except Exception as e:
      logger.error(
        f'Error processing consumption data from sender {sender} with data {data}: {str(e)}'
      )
      raise ConsumptionError(f'Failed to update consumption data: {str(e)}') from e

  def get_ven_status(self) -> Dict[str, Union[List[str], int]]:
    """
    Get current status information for all VENs.

    Returns:
        Dictionary containing VEN status information including:
        - List of pending VENs
        - List of active VENs
        - Total VEN count
    """
    return {
      'pending_vens': list(self._pending_vens),
      'active_vens': list(self._active_vens),
      'total_vens': len(self._pending_vens) + len(self._active_vens),
    }

  def get_current_consumption(self) -> float:
    """
    Get the current total consumption value.

    Returns:
        Current total consumption across all VENs
    """
    return self._current_consumption
