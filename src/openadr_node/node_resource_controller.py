from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
from threading import Lock

import pandas as pd

from src.openadr_node import logger
from src.openadr_node.models.event import ResourceConsumption
from src.openadr_node.database.loadprofile_manager import LoadProfileManager
from pydispatch import dispatcher


class NodeResourceController:
  """
  Controller for managing resource data updates, including load profiles and consumption data.

  Attributes
  ----------
  load_profile_manager : LoadProfileManager
      Manager for handling load profile data.
  ven_data : Dict[str, Dict[str, float]]
      Dictionary to store VEN data.
  current_consumption : float
      Current total consumption value.
  lock : Lock
      Lock to ensure thread safety.
  """

  def __init__(self, load_profile_manager: LoadProfileManager):
    """
    Initialize the ResourceController with a LoadProfileManager.

    Parameters
    ----------
    load_profile_manager : LoadProfileManager
        Manager for handling load profile data.
    """
    self._load_profile_manager = load_profile_manager
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._current_consumption = 0.0
    self._lock = Lock()

    self._z = None

  @staticmethod
  def process_load_profile_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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

    # Validate that each interval contains the required fields
    for interval in data:
      if not all(key in interval for key in ['dtstart', 'duration', 'signal_payload']):
        logger.error('Incomplete interval data: missing required fields')
        raise ValueError('Incomplete interval data: missing required fields')

    transformed_data = [
      {
        'dstart': int(interval['dtstart'].timestamp() * 1000),
        'duration': int(interval['duration'].total_seconds() * 1000),
        'signal_payload': interval['signal_payload'],
      }
      for interval in data
    ]

    return transformed_data

  def update_load_profile(self, sender: str, data: List[Dict[str, Any]]) -> None:
    """
    Update the load profile with the provided data.

    Parameters
    ----------
    sender : str
        The sender of the data.
    data : List[Dict[str, Any]]
        List of intervals containing load profile data.
    """
    # Check if the data is already formatted
    if not all(
      'dstart' in interval and 'duration' in interval and 'signal_payload' in interval
      for interval in data
    ):
      transformed_data = self.process_load_profile_data(data)
    else:
      transformed_data = data

    new_data_structure = {}

    current_unix_timestamp: int = int(datetime.now(timezone.utc).timestamp() * 1000)

    current_allowed_consumption = self._load_profile_manager.get_closest_point(
      current_unix_timestamp
    )
    current_consumption = self._load_profile_manager.get_closest_consumption_points(
      current_unix_timestamp
    )
    if current_consumption:
      current_consumption_df = pd.DataFrame(current_consumption)
      current_consumption_df = (
        current_consumption_df.groupby('ven_id')['value'].sum().reset_index()
      )
      current_consumption_df = current_consumption_df.rename(columns={'value': 'b'})
      df = current_consumption_df

    def correction_factor(G_i):
      return (5 * (G_i**2)) / 1.5 - (5 * G_i) / 1.5 + 1.085

    if current_allowed_consumption and current_consumption:
      try:
        # Step 1
        if self._z is None:
          unique_vens = self._load_profile_manager.get_unique_vens()
          self._z = current_allowed_consumption['signal_payload'] / unique_vens

        df['v'] = current_allowed_consumption['signal_payload']
        df['z'] = self._z
        df['g'] = df['z'] / df['b']
        df['w'] = (1 - df['g']) * df['b'] * correction_factor(df['g'])
        df['w_total'] = df['w'].sum()
        df['z_neu'] = df['w'] / df['w_total'] * df['v']

        print('-------')
        print(df)

        # Generate 95 intervals (15 minutes each) starting from current time
        base_time = datetime.now(timezone.utc)
        intervals = []
        for i in range(95):
          interval_time = base_time + timedelta(minutes=15 * i)
          intervals.append(
            {
              'dstart': int(interval_time.timestamp() * 1000),
              'duration': 900000,  # 15 minutes in milliseconds
              'signal_payload': 0,  # Default value, will be updated with z_neu
            }
          )

        # Create new_data_structure based on df values
        for _, row in df.iterrows():
          ven_id = row['ven_id']
          z_neu = row['z_neu']

          # Create a copy of intervals with the specific z_neu value
          ven_transformed_data = [
            {
              'dstart': interval['dstart'],
              'duration': interval['duration'],
              'signal_payload': z_neu,  # Use z_neu instead of random value
            }
            for interval in intervals
          ]
          new_data_structure[ven_id] = ven_transformed_data

      except Exception as e:
        print(f'Error123: {e}')
        raise

    self._load_profile_manager.insert_load_profile(transformed_data)
    dispatcher.send(sender='nm', signal='update_load_profile', data=new_data_structure)

  def update_consumption_data(self, sender: str, data: ResourceConsumption) -> None:
    """
    Update the consumption data with the provided ResourceConsumption data.

    Parameters
    ----------
    sender : str
        The sender of the data.
    data : ResourceConsumption
        Resource consumption data.
    """
    try:
      with self._lock:
        self._current_consumption = 0.0
        ven_data = self._ven_data.setdefault(data.ven_id, {})
        ven_data[data.resource_id] = data.data[1]

        self._current_consumption = sum(
          value for resources in self._ven_data.values() for value in resources.values()
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
          sender='nm', signal='update_consumption_data', data=self._current_consumption
        )
    except (AttributeError, IndexError) as e:
      logger.error(
        f'Error processing consumption data from sender {sender} with data {data}: {e}'
      )
      raise
