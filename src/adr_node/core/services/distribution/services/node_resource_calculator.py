from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple
import numpy as np
from numpy.typing import NDArray

from src.adr_node.core.services.distribution.interfaces.inode_resource_calculator import (
  INodeResourceCalculator,
)
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.openadr_node.errors.node_calculation_errors import (
  ProcessingError,
  CalculationError,
)
from src.openadr_node import logger


class NodeResourceCalculator(INodeResourceCalculator):
  """
  Handles load profile and consumption-related calculations for Virtual End Nodes (VENs).

  This class manages complex calculations related to load distribution, consumption analysis,
  and profile generation using dependency injection for services.
  """

  INTERVAL_DURATION_MS: int = 900000  # 15 minutes in milliseconds
  INTERVALS_PER_DAY: int = 1  # Number of 15-minute intervals in a day
  GMT_PLUS_ONE = timezone(timedelta(hours=1))

  CORRECTION_FACTOR_A: float = 5.0
  CORRECTION_FACTOR_B: float = 1.5
  CORRECTION_FACTOR_C: float = 1.085

  def __init__(
    self,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
  ):
    """
    Initialize the NodeResourceCalculator.

    Args:
        load_profile_service: Service for load profile operations
        consumption_service: Service for consumption operations
    """
    self._load_profile_service = load_profile_service
    self._consumption_service = consumption_service
    self._z: Optional[Union[float, NDArray[np.float64]]] = None

  def set_z_value(self, value: Optional[float]) -> None:
    """Set the z-value for load distribution calculations."""
    self._z = value

  @staticmethod
  def validate_intervals(data: List[Dict[str, Any]], required_fields: set) -> None:
    """Validate required fields in interval data."""
    for interval in data:
      if not required_fields.issubset(interval):
        logger.error('Incomplete interval data: missing required fields')
        raise ValueError('Incomplete interval data: missing required fields')

  @staticmethod
  def transform_intervals(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform load profile data into the desired format."""
    return [
      {
        'dstart': int(interval['dtstart'].timestamp() * 1000),
        'duration': int(interval['duration'].total_seconds() * 1000),
        'signal_payload': interval['signal_payload'],
      }
      for interval in data
    ]

  def process_load_profile_data(
    self, data: List[Dict[str, Any]]
  ) -> List[Dict[str, Any]]:
    """Process and validate load profile data."""
    if not isinstance(data, list):
      logger.error('Invalid data format: expected list of intervals')
      raise ValueError('Invalid data format: expected list of intervals')

    required_fields = {'dtstart', 'duration', 'signal_payload'}
    self.validate_intervals(data, required_fields)
    return self.transform_intervals(data)

  def get_current_data(
    self, current_timestamp: int
  ) -> tuple[Optional[dict], Optional[list]]:
    """Get current allowed consumption and consumption points."""
    result = self._load_profile_service.get_closest_load_point(current_timestamp)
    if not result.success:
      return None, None

    consumption_result = self._consumption_service.get_closest_consumption_points(
      current_timestamp
    )
    consumption_points = (
      consumption_result.data.get('consumption_points', [])
      if consumption_result.success
      else []
    )

    return result.data, consumption_points

  @staticmethod
  def prepare_consumption_array(
    current_consumption: List[Dict[str, Any]],
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    """Convert consumption data into NumPy arrays using vectorized operations."""
    if not current_consumption:
      return np.array([], dtype=str), np.array([], dtype=np.float64)

    try:
      ven_ids = np.array([item['ven_id'] for item in current_consumption], dtype=str)
      values = np.array(
        [item['value'] for item in current_consumption], dtype=np.float64
      )

      unique_vens, indices = np.unique(ven_ids, return_inverse=True)
      summed_values = np.zeros(len(unique_vens))
      np.add.at(summed_values, indices, values)

      return unique_vens, summed_values
    except Exception as e:
      logger.error(f'Failed to prepare consumption array: {str(e)}')
      raise ProcessingError(f'Consumption array preparation failed: {str(e)}') from e

  @staticmethod
  def correction_factor(G_i: NDArray[np.float64]) -> NDArray[np.float64]:
    """Calculate correction factor using vectorized operations."""
    return (
      (NodeResourceCalculator.CORRECTION_FACTOR_A * np.square(G_i))
      / NodeResourceCalculator.CORRECTION_FACTOR_B
      - (NodeResourceCalculator.CORRECTION_FACTOR_A * G_i)
      / NodeResourceCalculator.CORRECTION_FACTOR_B
      + NodeResourceCalculator.CORRECTION_FACTOR_C
    )

  def calculate_z_value(
    self,
    current_allowed_consumption: Dict[str, Any],
    active_vens_count: int,
    pending_vens_count: int,
  ) -> float:
    """Calculate the initial Z value for load distribution."""
    if active_vens_count < 0 or pending_vens_count < 0:
      raise ValueError('VEN counts cannot be negative')

    try:
      if active_vens_count == 0:
        total_ven_count = max(pending_vens_count + active_vens_count, 1)
        return current_allowed_consumption['signal_payload'] / total_ven_count

      if self._z is None:
        self._z = current_allowed_consumption['signal_payload'] / active_vens_count
      return float(self._z)
    except Exception as e:
      logger.error(f'Failed to calculate Z value: {str(e)}')
      raise CalculationError(f'Z value calculation failed: {str(e)}') from e

  def calculate_load_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    total_allowed: float,
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    """Calculate load distribution using vectorized operations."""
    try:
      z = (
        np.full_like(consumption_values, self._z)
        if not isinstance(self._z, np.ndarray)
        or self._z.shape != consumption_values.shape
        else self._z
      )
      with np.errstate(divide='ignore', invalid='ignore'):
        g = np.divide(
          z,
          consumption_values,
          out=np.zeros_like(z),
          where=consumption_values != 0,
        )
        g = np.nan_to_num(g)
        g = np.clip(g, 0, 0.8)
      w = (1 - g) * consumption_values * self.correction_factor(g)
      w_total = np.sum(w)
      z_neu = w / w_total * total_allowed if w_total > 0 else np.zeros_like(w)
      return ven_ids, z_neu
    except Exception as e:
      logger.error(f'Failed to calculate load distribution: {str(e)}')
      raise CalculationError(f'Load distribution calculation failed: {str(e)}') from e

  def generate_time_intervals(self) -> List[Dict[str, Any]]:
    """Generate time intervals for a full day."""
    try:
      gmt_plus_one_now = datetime.now(self.GMT_PLUS_ONE)
      second = (gmt_plus_one_now.second // 30) * 30
      start_of_day = gmt_plus_one_now.replace(second=second, microsecond=0)
      base_timestamp = int(start_of_day.timestamp() * 1000)

      intervals = np.arange(self.INTERVALS_PER_DAY) * self.INTERVAL_DURATION_MS
      return [
        {
          'dstart': base_timestamp + int(offset),
          'duration': self.INTERVAL_DURATION_MS,
          'signal_payload': 0,
        }
        for offset in intervals
      ]
    except Exception as e:
      logger.error(f'Failed to generate time intervals: {str(e)}')
      raise ProcessingError(f'Time interval generation failed: {str(e)}') from e
