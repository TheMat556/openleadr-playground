from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from threading import Lock
from functools import reduce

import numpy as np
from pydispatch import dispatcher

from src.openadr_node.database.loadprofile_manager import LoadProfileManager, logger
from src.openadr_node.models.event import ResourceConsumption


class NodeResourceController:
  def __init__(self, load_profile_manager: LoadProfileManager):
    self._load_profile_manager = load_profile_manager
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._current_consumption = 0.0
    self._lock = Lock()
    self._z = None

  def _validate_intervals_recursive(
    self, data: List[Dict[str, Any]], required_fields: set, index: int = 0
  ) -> None:
    """Recursively validate that each interval contains the required fields."""
    if index >= len(data):
      return
    interval = data[index]
    if not required_fields.issubset(interval):
      logger.error('Incomplete interval data: missing required fields')
      raise ValueError('Incomplete interval data: missing required fields')
    self._validate_intervals_recursive(data, required_fields, index + 1)

  @staticmethod
  def _transform_intervals_no_loop(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform load profile data into the desired format using map."""

    def transform(interval):
      return {
        'dstart': int(interval['dtstart'].timestamp() * 1000),
        'duration': int(interval['duration'].total_seconds() * 1000),
        'signal_payload': interval['signal_payload'],
      }

    return list(map(transform, data))

  def process_load_profile_data(
    self, data: List[Dict[str, Any]]
  ) -> List[Dict[str, Any]]:
    """
    Process the load profile data.
    Parameters
    ----------
    data : List[Dict[str, Any]]
        List of intervals containing load profile data.
    Returns
    -------
    List[Dict[str, Any]]
        Transformed load profile data.
    """
    if not isinstance(data, list):
      logger.error('Invalid data format: expected list of intervals')
      raise ValueError('Invalid data format: expected list of intervals')

    required_fields = {'dtstart', 'duration', 'signal_payload'}

    # Since we must remove explicit loops, use recursion for validation
    self._validate_intervals_recursive(data, required_fields, 0)

    # Transform the data without a for-loop
    return self._transform_intervals_no_loop(data)

  def _get_current_data(
    self, current_timestamp: int
  ) -> tuple[Optional[dict], Optional[list]]:
    """Get current allowed consumption and consumption points."""
    current_allowed_consumption = self._load_profile_manager.get_closest_point(
      current_timestamp
    )
    current_consumption = self._load_profile_manager.get_closest_consumption_points(
      current_timestamp
    )
    return current_allowed_consumption, current_consumption

  def _prepare_consumption_array(
    self, current_consumption: List[Dict[str, Any]]
  ) -> tuple[np.ndarray, np.ndarray]:
    """Convert consumption data into NumPy arrays for values and VEN IDs."""
    if not current_consumption:
      return np.array([]), np.array([])

    # Use map instead of a loop
    ven_ids = np.array(list(map(lambda item: item['ven_id'], current_consumption)))
    values = np.array(
      list(map(lambda item: item['value'], current_consumption)), dtype=np.float64
    )

    # Use NumPy unique and add.at to avoid explicit Python loops
    unique_vens, indices = np.unique(ven_ids, return_inverse=True)
    summed_values = np.zeros(len(unique_vens))
    np.add.at(summed_values, indices, values)

    return unique_vens, summed_values

  @staticmethod
  def _correction_factor(G_i: np.ndarray) -> np.ndarray:
    """Calculate the correction factor for given G_i values using vectorized operations."""
    return (5 * np.square(G_i)) / 1.5 - (5 * G_i) / 1.5 + 1.085

  def _calculate_z_value(
    self, current_allowed_consumption: Dict[str, Any], unique_ven_count: int
  ) -> float:
    """Calculate initial Z value if not already set."""
    if self._z is None:
      self._z = current_allowed_consumption['signal_payload'] / unique_ven_count
    return self._z

  def _calculate_load_distribution(
    self, ven_ids: np.ndarray, consumption_values: np.ndarray, total_allowed: float
  ) -> tuple[np.ndarray, np.ndarray]:
    """Calculate load distribution parameters for each VEN using vectorized operations."""
    z = np.full_like(consumption_values, self._z)
    g = np.divide(z, consumption_values, where=consumption_values != 0)
    w = (1 - g) * consumption_values * self._correction_factor(g)
    w_total = np.sum(w)
    z_neu = w / w_total * total_allowed if w_total > 0 else np.zeros_like(w)

    return ven_ids, z_neu

  @staticmethod
  def generate_time_intervals() -> List[Dict[str, Any]]:
    """
    Generate 96 intervals of 15 minutes each, starting at 00:00 for GMT+1.
    """
    gmt_plus_one = timezone(timedelta(hours=1))

    gmt_plus_one_now = datetime.now(gmt_plus_one)

    start_of_day_gmt_plus_one = gmt_plus_one_now.replace(
      hour=0, minute=0, second=0, microsecond=0
    )

    base_timestamp = start_of_day_gmt_plus_one.timestamp() * 1000

    intervals = np.arange(96) * 15 * 60 * 1000

    def make_interval(offset_ms):
      return {
        'dstart': int(base_timestamp + offset_ms),
        'duration': 900000,  # 15 minutes in milliseconds
        'signal_payload': 0,
      }

    return list(map(make_interval, intervals))

  def _create_ven_profiles(
    self, ven_ids: np.ndarray, z_neu: np.ndarray, intervals: List[Dict[str, Any]]
  ) -> Dict[str, List[Dict[str, Any]]]:
    """Create load profiles for each VEN based on calculated z_neu values without an explicit loop."""

    # We'll zip up ven_ids and z_neu, then build a dict
    def build_profile(pair):
      ven_id, z_value = pair

      def apply_value(interval):
        new_interval = {**interval}
        new_interval['signal_payload'] = z_value
        return new_interval

      return str(ven_id), list(map(apply_value, intervals))

    pairs = zip(ven_ids, z_neu)
    # Create a list of (ven_id_str, intervals_list) pairs
    pair_list = list(map(build_profile, pairs))
    # Turn that into a dict
    return dict(pair_list)

  def update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
    """Update the load profile with the provided data."""
    # Fetch and log latest z-values (no explicit loop)
    print('update_load_profile!')
    try:
      latest_z_values = self._load_profile_manager.get_latest_z_values()
      if latest_z_values:
        logger.info('Current Z-values for VENs:')
        # Use map to log each z_value
        list(
          map(
            lambda z_val: logger.info(
              f"VEN: {z_val['ven_id']}, Z-value: {z_val['z_value']}"
            ),
            latest_z_values,
          )
        )
      else:
        logger.info('No previous Z-values found in database')
    except Exception as e:
      logger.error(f'Error retrieving Z-values: {e}')

    # Transform data if needed without a loop
    def is_transformed(interval):
      return all(k in interval for k in ['dstart', 'duration', 'signal_payload'])

    # Check if all intervals are already in the correct format
    if not all(map(is_transformed, data)):
      transformed_data = self.process_load_profile_data(data)
    else:
      transformed_data = data

    current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    current_allowed_consumption, current_consumption = self._get_current_data(
      current_timestamp
    )

    new_data_structure = {}
    if current_allowed_consumption and current_consumption:
      try:
        ven_ids, consumption_values = self._prepare_consumption_array(
          current_consumption
        )
        if len(ven_ids) > 0:
          self._z = self._calculate_z_value(current_allowed_consumption, len(ven_ids))
          ven_ids, z_neu = self._calculate_load_distribution(
            ven_ids,
            consumption_values,
            current_allowed_consumption['signal_payload'],
          )
          self._load_profile_manager.insert_z_values(ven_ids, z_neu, current_timestamp)
          intervals = self.generate_time_intervals()
          new_data_structure = self._create_ven_profiles(ven_ids, z_neu, intervals)
      except Exception as e:
        logger.error(f'Error calculating load distribution: {e}')
        raise

    self._load_profile_manager.insert_load_profile(transformed_data)
    dispatcher.send(sender='nm', signal='update_load_profile', data=new_data_structure)

  def update_consumption_data(self, sender: str, data: ResourceConsumption) -> None:
    """
    Update the consumption data with the provided ResourceConsumption data.
    """
    try:
      with self._lock:
        self._current_consumption = 0.0
        ven_data = self._ven_data.setdefault(data.ven_id, {})
        ven_data[data.resource_id] = data.data[1]

        # Use reduce for summation to avoid explicit loops
        self._current_consumption = reduce(
          lambda acc, d: acc + reduce(lambda acc2, val: acc2 + val, d.values(), 0.0),
          self._ven_data.values(),
          0.0,
        )

        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        consumption_data = {
          'timestamp': timestamp_ms,
          'ven_id': data.ven_id,
          'resource_id': data.resource_id,
          'value': data.data[1],
        }
        self._load_profile_manager.insert_consumption(consumption_data)

        logger.debug(f'Updated consumption data - Total: {self._current_consumption}')
        dispatcher.send(
          sender='nm',
          signal='update_consumption_data',
          data=self._current_consumption,
        )
    except (AttributeError, IndexError) as e:
      logger.error(
        f'Error processing consumption data from sender {sender} with data {data}: {e}'
      )
      raise
