import logging
from typing import List, Dict, Any
import pandas as pd

from src.openadr_node.database.database_manager import DatabaseManager, DatabaseError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadProfileManager:
  def __init__(self, db_manager: DatabaseManager):
    """
    Initialize the LoadProfileManager

    Args:
        db_manager (DatabaseManager): An instance of DatabaseManager
    """
    self.db_manager = db_manager
    self._initialize_database()

  def _initialize_database(self):
    """Initialize the database tables for load profiles and consumption"""
    try:
      self.db_manager.connect()
      self.db_manager.create_table(
        'load_profiles',
        {
          'dstart': 'INTEGER PRIMARY KEY',
          'duration': 'INTEGER NOT NULL',
          'signal_payload': 'FLOAT NOT NULL',
        },
      )
      self.db_manager.create_table(
        'consumption',
        {
          'timestamp': 'INTEGER PRIMARY KEY',
          'ven_id': 'TEXT NOT NULL',
          'resource_id': 'TEXT NOT NULL',
          'value': 'FLOAT NOT NULL',
        },
      )
    except DatabaseError as e:
      logger.error(f'Failed to initialize database: {e}')
      raise

  def convert_load_profile(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Generate a load profile DataFrame from the given data

    Args:
        data (List[Dict[str, Any]]): List of intervals with dtstart and signal_payload

    Returns:
        pd.DataFrame: Transformed load profile DataFrame
    """
    transformed_data = [
      {
        'dstart': int(
          interval['dtstart'].timestamp() * 1000
        ),  # Convert to Unix timestamp in milliseconds
        'duration': int(
          interval['duration'].total_seconds() * 1000
        ),  # Convert duration to milliseconds
        'signal_payload': interval['signal_payload'],
      }
      for interval in data
    ]
    df = pd.DataFrame(transformed_data)
    df.set_index('dstart', inplace=True)  # Set the Unix timestamp as the index
    return df

  def insert_load_profile(self, data: List[Dict[str, Any]]) -> None:
    """
    Insert the load profile data into the database using batch processing.

    Args:
        data (List[Dict[str, Any]]): List of dictionaries containing load profile data
            with 'dstart', 'duration', and 'signal_payload' keys.
    """
    if not data:
      logger.warning('No data provided for insertion')
      return

    try:
      # Prepare batch values
      batch_values = [
        [interval['dstart'], interval['duration'], interval['signal_payload']]
        for interval in data
      ]

      # Perform batch insert
      self.db_manager.insert_values_batch(
        table_name='load_profiles',
        columns=['dstart', 'duration', 'signal_payload'],
        batch_values=batch_values,
        replace=True,
        batch_size=1000,  # Adjust this value based on your needs
      )

      logger.info(f'Successfully inserted {len(data)} load profile records')

    except (DatabaseError, KeyError) as e:
      logger.error(f'Failed to insert load profile batch: {str(e)}')
      raise

  def insert_consumption_batch(self, data: List[Dict[str, Any]]) -> None:
    """
    Insert multiple consumption records into the database using batch processing.

    Args:
        data (List[Dict[str, Any]]): List of dictionaries containing consumption data
            with 'timestamp', 'ven_id', 'resource_id', and 'value' keys.
    """
    if not data:
      logger.warning('No consumption data provided for insertion')
      return

    try:
      # Prepare batch values
      batch_values = [
        [record['timestamp'], record['ven_id'], record['resource_id'], record['value']]
        for record in data
      ]

      # Perform batch insert
      self.db_manager.insert_values_batch(
        table_name='consumption',
        columns=['timestamp', 'ven_id', 'resource_id', 'value'],
        batch_values=batch_values,
        replace=True,
        batch_size=1000,  # Adjust this value based on your needs
      )

      logger.info(f'Successfully inserted {len(data)} consumption records')

    except (DatabaseError, KeyError) as e:
      logger.error(f'Failed to insert consumption batch: {str(e)}')
      raise

  def get_load_profile(self) -> pd.DataFrame:
    """
    Retrieve the load profile data from the database.

    Returns:
        pd.DataFrame: Load profile DataFrame
    """
    query = 'SELECT dstart, duration, signal_payload FROM load_profiles'
    rows = self.db_manager.execute_query(query)
    df = pd.DataFrame(rows)

    if not df.empty:
      df.set_index('dstart', inplace=True)
    return df

  def insert_consumption(self, data: Dict[str, Any]) -> None:
    """
    Insert a single consumption record into the database.

    Args:
        data (Dict[str, Any]): Dictionary with consumption data.
    """
    self.insert_consumption_batch([data])

  def get_consumption(self) -> pd.DataFrame:
    """
    Retrieve the consumption data from the database.

    Returns:
        pd.DataFrame: Consumption DataFrame
    """
    query = 'SELECT timestamp, ven_id, resource_id, value FROM consumption'
    rows = self.db_manager.execute_query(query)
    df = pd.DataFrame(rows)

    if not df.empty:
      df.set_index('timestamp', inplace=True)
    return df
