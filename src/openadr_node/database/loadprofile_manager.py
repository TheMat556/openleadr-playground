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
    Insert the load profile data into the database.

    Args:
        data (Dict[str, Any]): Dictionary with Unix timestamps as keys and signal payloads as values.
    """

    # Insert values into the database
    for interval in data:
      self.db_manager.insert_values(
        table_name='load_profiles',
        columns=['dstart', 'duration', 'signal_payload'],
        values=[interval['dstart'], interval['duration'], interval['signal_payload']],
        replace=True,
      )

  def get_load_profile(self) -> pd.DataFrame:
    """
    Retrieve the load profile data from the database.

    Returns:
        pd.DataFrame: Load profile DataFrame
    """
    query = 'SELECT dstart, duration, signal_payload FROM load_profiles'
    connection, cursor = self.db_manager._get_connection()
    cursor.execute(query)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['dstart', 'duration', 'signal_payload'])

    if not df.empty:
      df.set_index('dstart', inplace=True)
    return df

  def insert_consumption(self, data: Dict[str, Any]) -> None:
    """
    Insert the consumption data into the database.

    Args:
        data (Dict[str, Any]): Dictionary with consumption data.
    """

    # Insert values into the database
    self.db_manager.insert_values(
      table_name='consumption',
      columns=['timestamp', 'ven_id', 'resource_id', 'value'],
      values=[data['timestamp'], data['ven_id'], data['resource_id'], data['value']],
      replace=True,
    )

  def get_consumption(self) -> pd.DataFrame:
    """
    Retrieve the consumption data from the database.

    Returns:
        pd.DataFrame: Consumption DataFrame
    """
    query = 'SELECT timestamp, ven_id, resource_id, value FROM consumption'
    connection, cursor = self.db_manager._get_connection()
    cursor.execute(query)
    rows = cursor.fetchall()
    df = pd.DataFrame(rows, columns=['timestamp', 'ven_id', 'resource_id', 'value'])

    if not df.empty:
      df.set_index('timestamp', inplace=True)
    return df
