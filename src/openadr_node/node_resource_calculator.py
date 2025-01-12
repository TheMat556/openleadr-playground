from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Union, Tuple

import numpy as np
from numpy.typing import NDArray

from src.openadr_node.database.loadprofile_manager import LoadProfileManager, logger
from src.openadr_node.errors.node_calculation_errors import (
  ProcessingError,
  CalculationError,
)


@dataclass
class TimeInterval:
  """Data class representing a time interval with load profile data."""

  dstart: int
  duration: int
  signal_payload: float


class NodeResourceCalculator:
  """
  Handles load profile and consumption-related calculations for Virtual End Nodes (VENs).

  This class manages complex calculations related to load distribution, consumption analysis,
  and profile generation. It uses vectorized operations for efficient computation and
  maintains a functional programming approach where possible.

  Args:
      load_profile_manager: Manager instance for handling load profiles

  Attributes:
      _z: Distribution factor for load calculations
  """

  INTERVAL_DURATION_MS: int = 900000  # 15 minutes in milliseconds
  INTERVALS_PER_DAY: int = 1  # Number of 15-minute intervals in a day
  GMT_PLUS_ONE = timezone(timedelta(hours=1))

  CORRECTION_FACTOR_A: float = 5.0
  CORRECTION_FACTOR_B: float = 1.5
  CORRECTION_FACTOR_C: float = 1.085

  def __init__(self, load_profile_manager: LoadProfileManager):
    """
    Initialize the NodeResourceCalculator.

    :param load_profile_manager: Instance of LoadProfileManager to handle database operations.
    """
    self._load_profile_manager = load_profile_manager
    self._z: Optional[Union[float, NDArray[np.float64]]] = None

  def set_z_value(self, value: Optional[float]) -> None:
    """Set the z-value for load distribution calculations."""
    self._z = value

  @staticmethod
  def validate_intervals(data: List[Dict[str, Any]], required_fields: set) -> None:
    for interval in data:
      if not required_fields.issubset(interval):
        logger.error('Incomplete interval data: missing required fields')
        raise ValueError('Incomplete interval data: missing required fields')

  @staticmethod
  def transform_intervals(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform load profile data into the desired format using a loop.

    :param data: List of intervals to transform.
    :return: Transformed list of intervals.
    """
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
    """
    Validate and transform the load profile data into the desired format.

    :param data: List of intervals containing load profile data.
    :return: Transformed list of intervals.
    :raises ValueError: If the data format is invalid.
    """
    if not isinstance(data, list):
      logger.error('Invalid data format: expected list of intervals')
      raise ValueError('Invalid data format: expected list of intervals')

    required_fields = {'dtstart', 'duration', 'signal_payload'}

    self.validate_intervals(data, required_fields)
    return self.transform_intervals(data)

  def get_current_data(
    self, current_timestamp: int
  ) -> tuple[Optional[dict], Optional[list]]:
    """
    Get current allowed consumption and consumption points.

    :param current_timestamp: Current timestamp in milliseconds.
    :return: Tuple containing current allowed consumption and consumption points.
    """
    current_allowed_consumption = self._load_profile_manager.get_closest_point(
      current_timestamp
    )
    current_consumption = self._load_profile_manager.get_closest_consumption_points(
      current_timestamp
    )
    return current_allowed_consumption, current_consumption

  @staticmethod
  def prepare_consumption_array(
    current_consumption: List[Dict[str, Any]],
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    """
    Convert consumption data into NumPy arrays using vectorized operations.

    Args:
        current_consumption: List of consumption data points

    Returns:
        Tuple of VEN IDs array and consumption values array

    Raises:
        ProcessingError: If consumption array preparation fails
    """
    if not current_consumption:
      return np.array([], dtype=str), np.array([], dtype=np.float64)

    try:
      # Extract ven_ids and values directly from the list of dictionaries
      ven_ids = np.array([item['ven_id'] for item in current_consumption], dtype=str)
      values = np.array(
        [item['value'] for item in current_consumption], dtype=np.float64
      )

      # Get unique VENs and sum their values
      unique_vens, indices = np.unique(ven_ids, return_inverse=True)
      summed_values = np.zeros(len(unique_vens))
      np.add.at(summed_values, indices, values)

      return unique_vens, summed_values
    except Exception as e:
      logger.error(f'Failed to prepare consumption array: {str(e)}')
      raise ProcessingError(f'Consumption array preparation failed: {str(e)}') from e

  @staticmethod
  def correction_factor(G_i: NDArray[np.float64]) -> NDArray[np.float64]:
    """
    Calculate correction factor using vectorized operations.

    Args:
        G_i: Array of G values

    Returns:
        Array of correction factors
    """
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
    """
    Calculate the initial Z value for load distribution.

    Args:
        current_allowed_consumption: Current consumption limits
        active_vens_count: Number of active VENs
        pending_vens_count: Number of pending VENs

    Returns:
        Calculated Z value

    Raises:
        ValueError: If invalid VEN counts are provided
    """
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

  @staticmethod
  def process_latest_z_values(
    latest_z_values: List[Dict[str, Any]], ven_ids: NDArray[np.str_]
  ) -> Optional[NDArray[np.float64]]:
    """
    Process Z values into a numpy array aligned with VEN IDs.

    Args:
        latest_z_values: List of latest Z values
        ven_ids: Array of VEN IDs

    Returns:
        Array of processed Z values or None if no values available
    """
    if not latest_z_values:
      return None

    try:
      z_map = {item['ven_id']: item['z_value'] for item in latest_z_values}
      return np.array([z_map.get(ven_id, 0.0) for ven_id in ven_ids])
    except Exception as e:
      logger.error(f'Failed to process Z values: {str(e)}')
      return None

  def calculate_load_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    total_allowed: float,
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    """
    Calculate load distribution using vectorized operations.

    Args:
        ven_ids: Array of VEN IDs
        consumption_values: Array of consumption values
        total_allowed: Total allowed consumption

    Returns:
        Tuple of VEN IDs and their corresponding Z values

    Raises:
        CalculationError: If calculation fails
    """
    try:
      z = (
        np.full_like(consumption_values, self._z)
        if not isinstance(self._z, np.ndarray)
        or self._z.shape != consumption_values.shape
        else self._z
      )
      # Avoid division by zero
      with np.errstate(divide='ignore', invalid='ignore'):
        g = np.divide(
          z, consumption_values, out=np.zeros_like(z), where=consumption_values != 0
        )
        g = np.nan_to_num(g)
      w = (1 - g) * consumption_values * self.correction_factor(g)
      w_total = np.sum(w)
      if w_total > 0:
        z_neu = w / w_total * total_allowed
      else:
        z_neu = np.zeros_like(w)
      return ven_ids, z_neu
    except Exception as e:
      logger.error(f'Failed to calculate load distribution: {str(e)}')
      raise CalculationError(f'Load distribution calculation failed: {str(e)}') from e

  def generate_time_intervals(self) -> List[Dict[str, Any]]:
    """
    Generate time intervals for a full day.

    Returns:
        List of time intervals
    """
    try:
      gmt_plus_one_now = datetime.now(self.GMT_PLUS_ONE)
      # minute = (gmt_plus_one_now.minute // 15) * 15
      second = (gmt_plus_one_now.second // 30) * 30
      # minute = gmt_plus_one_now.minute
      # start_of_day = gmt_plus_one_now.replace(minute=minute, second=0, microsecond=0)
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

  @staticmethod
  def create_ven_profiles(
    ven_ids: NDArray[np.str_],
    z_neu: NDArray[np.float64],
    intervals: List[Dict[str, Any]],
  ) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create load profiles for VENs using functional programming approach.

    Args:
        ven_ids: Array of VEN IDs
        z_neu: Array of Z values
        intervals: List of time intervals

    Returns:
        Dictionary mapping VEN IDs to their load profiles

    Raises:
        ProcessingError: If profile creation fails
    """
    try:
      if ven_ids.size == 0 or z_neu.size == 0:
        logger.error('VEN IDs or Z values are empty')
        raise ProcessingError('VEN IDs and Z values must not be empty')

      def build_profile(pair: Tuple[str, float]) -> Tuple[str, List[Dict[str, Any]]]:
        ven_id, z_value = pair
        return str(ven_id), [
          {**interval, 'signal_payload': float(z_value)} for interval in intervals
        ]

      return dict(map(build_profile, zip(ven_ids, z_neu)))
    except Exception as e:
      logger.error(f'Failed to create VEN profiles: {str(e)}')
      raise ProcessingError(f'VEN profile creation failed: {str(e)}') from e
