import random
from datetime import datetime, timezone
from typing import List, Dict, Any
from threading import Lock
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

    new_data_structure = {}
    # put the logic for fair distribution here
    for ven_id in self._ven_data.keys():
      ven_transformed_data = [
        {
          'dstart': interval['dstart'],
          'duration': interval['duration'],
          'signal_payload': interval['signal_payload'] * random.random(),
        }
        for interval in transformed_data
      ]
      new_data_structure[ven_id] = ven_transformed_data

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
