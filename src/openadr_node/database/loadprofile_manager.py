import logging
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd

from src.openadr_node.database.database_manager import DatabaseManager, DatabaseError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadProfileManager:
  def __init__(self, db_manager: DatabaseManager, batch_size: int = 1000):
    """
    Initialize the LoadProfileManager

    Args:
        db_manager (DatabaseManager): An instance of DatabaseManager
    """
    self.batch_size = batch_size
    self.db_manager = db_manager
    self._initialize_database()

  def _initialize_database(self):
    """Initialize the database tables for load profiles, consumption, and z-values"""
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
      # New table for z-values
      self.db_manager.create_table(
        'z_values',
        {
          'timestamp': 'INTEGER NOT NULL',
          'ven_id': 'TEXT NOT NULL',
          'z_value': 'FLOAT NOT NULL',
          'PRIMARY KEY': '(timestamp, ven_id)',
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

  def insert_load_profile(
    self, data: List[Dict[str, Any]]
  ) -> Dict[str, int | List[Any]]:
    """
    Insert the load profile data into the database using batch processing.

    Args:
        data (List[Dict[str, Any]]): List of dictionaries containing load profile data
            with 'dstart', 'duration', and 'signal_payload' keys.
    """
    if not data:
      logger.warning('No data provided for insertion')
      return {'success': 0, 'failed': 0, 'errors': []}

    results = {'success': 0, 'failed': 0, 'errors': []}

    for i in range(0, len(data), self.batch_size):
      batch = data[i : i + self.batch_size]
      batch_values = []

      for interval in batch:
        try:
          # Validate data before adding to batch
          if not all(k in interval for k in ['dstart', 'duration', 'signal_payload']):
            raise ValueError(f'Missing required fields in record: {interval}')

          batch_values.append(
            [interval['dstart'], interval['duration'], interval['signal_payload']]
          )
        except Exception as e:
          results['failed'] += 1
          results['errors'].append({'data': interval, 'error': str(e)})
          logger.error(f'Failed to process record: {str(e)}')
          continue

      if batch_values:
        try:
          self.db_manager.insert_values_batch(
            table_name='load_profiles',
            columns=['dstart', 'duration', 'signal_payload'],
            batch_values=batch_values,
            replace=True,
          )
          results['success'] += len(batch_values)
        except DatabaseError as e:
          results['failed'] += len(batch_values)
          results['errors'].append({'batch': batch_values, 'error': str(e)})
          logger.error(f'Failed to insert batch: {str(e)}')

    logger.info(
      f"Insertion complete. Succeeded: {results['success']}, Failed: {results['failed']}"
    )
    return results

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
        batch_size=self.batch_size,  # Adjust this value based on your needs
      )

      logger.info(f'Successfully inserted {len(data)} consumption records')

    except (DatabaseError, KeyError) as e:
      logger.error(f'Failed to insert consumption batch: {str(e)}')
      raise

  def get_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'dstart ASC',
  ) -> pd.DataFrame:
    """
    Retrieve the load profile data from the database with ordered pagination.

    Args:
        limit: Optional[int] - Maximum number of records to return
        offset: Optional[int] - Number of records to skip
        order_by: str - Column and direction to order by (default: 'dstart ASC')

    Returns:
        pd.DataFrame: Load profile data
    """
    base_query = f"""
                SELECT dstart, duration, signal_payload
                FROM load_profiles
                ORDER BY {order_by}
            """

    params = []
    if limit is not None:
      base_query += ' LIMIT ?'
      params.append(limit)

    if offset is not None:
      base_query += ' OFFSET ?'
      params.append(offset)

    try:
      rows = self.db_manager.execute_query(base_query, params)
      df = pd.DataFrame(rows)

      if not df.empty:
        df.set_index('dstart', inplace=True)
      return df
    except DatabaseError as e:
      logger.error(f'Failed to retrieve load profile data: {str(e)}')
      raise

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

  def get_unique_vens(self) -> int:
    """
    Retrieve the number of unique VENs in the consumption data.

    Returns:
        int: Number of unique VENs
    """
    query = 'SELECT DISTINCT ven_id FROM consumption'
    rows = self.db_manager.execute_query(query)
    print('ROWS', rows)
    return len(rows)

  def get_closest_point(self, target_timestamp):
    query = """
        SELECT dstart, duration, signal_payload
        FROM load_profiles
        ORDER BY ABS(dstart - ?) ASC
        LIMIT 1
    """
    params = (target_timestamp,)
    rows = self.db_manager.execute_query(query, params)
    return rows[0] if rows else None

  def get_closest_consumption_points(self, target_timestamp):
    """
    Retrieve the nearest consumption point for each unique ven_id to the given timestamp.

    Args:
        target_timestamp (int): The target timestamp to search for.

    Returns:
        List[Dict[str, Any]]: A list of the nearest consumption point records for each unique ven_id.
    """
    query = """
        SELECT t1.timestamp, t1.ven_id, t1.resource_id, t1.value
        FROM consumption t1
        INNER JOIN (
            SELECT ven_id, MIN(ABS(timestamp - ?)) AS min_diff
            FROM consumption
            GROUP BY ven_id
        ) t2
        ON t1.ven_id = t2.ven_id AND ABS(t1.timestamp - ?) = t2.min_diff
    """
    params = (target_timestamp, target_timestamp)
    rows = self.db_manager.execute_query(query, params)
    return rows if rows else []

  def insert_z_values(
    self, ven_ids: np.ndarray, z_values: np.ndarray, timestamp: int
  ) -> None:
    """
    Insert z-values for multiple VENs into the database.

    Args:
        ven_ids (np.ndarray): Array of VEN IDs
        z_values (np.ndarray): Array of z-values corresponding to the VEN IDs
        timestamp (int): Current timestamp in milliseconds
    """
    try:
      batch_values = [
        [timestamp, str(ven_id), float(z_value)]
        for ven_id, z_value in zip(ven_ids, z_values)
      ]

      self.db_manager.insert_values_batch(
        table_name='z_values',
        columns=['timestamp', 'ven_id', 'z_value'],
        batch_values=batch_values,
        replace=True,
      )
      logger.info(f'Successfully inserted {len(batch_values)} z-values')
    except DatabaseError as e:
      logger.error(f'Failed to insert z-values: {str(e)}')
      raise

  def get_latest_z_values(self) -> List[Dict[str, Any]]:
    """
    Retrieve the most recent z-value for each VEN.

    Returns:
        List[Dict[str, Any]]: List of dictionaries containing the latest z-values
    """
    query = """
          SELECT t1.timestamp, t1.ven_id, t1.z_value
          FROM z_values t1
          INNER JOIN (
              SELECT ven_id, MAX(timestamp) as max_timestamp
              FROM z_values
              GROUP BY ven_id
          ) t2
          ON t1.ven_id = t2.ven_id AND t1.timestamp = t2.max_timestamp
      """
    try:
      rows = self.db_manager.execute_query(query)
      return rows
    except DatabaseError as e:
      logger.error(f'Failed to retrieve latest z-values: {str(e)}')
      raise
