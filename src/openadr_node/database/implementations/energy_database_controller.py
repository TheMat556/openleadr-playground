from typing import List, Dict, Any, Optional

import numpy as np

from src.openadr_node import logger
from src.openadr_node.database.interfaces.database_interface import IDatabaseManager
from src.openadr_node.database.database_manager import DatabaseError
from src.openadr_node.database.interfaces.database_interface import (
  IEnergyDatabaseController,
)


class EnergyDatabaseController(IEnergyDatabaseController):
  def __init__(self, db_manager: IDatabaseManager, batch_size: int = 1000):
    """
    Initialize the EnergyDatabaseController

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
      float_not_null = 'FLOAT NOT NULL'
      text_not_null = 'TEXT NOT NULL'

      self.db_manager.create_table(
        'load_profiles',
        {
          'dstart': 'INTEGER PRIMARY KEY UNIQUE',
          'duration': 'INTEGER NOT NULL',
          'signal_payload': float_not_null,
        },
      )
      self.db_manager.create_table(
        'consumption',
        {
          'timestamp': 'INTEGER PRIMARY KEY',
          'ven_id': text_not_null,
          'resource_id': text_not_null,
          'value': float_not_null,
        },
      )
      # New table for z-values
      self.db_manager.create_table(
        'z_values',
        {
          'timestamp': 'INTEGER NOT NULL',
          'ven_id': text_not_null,
          'z_value': float_not_null,
          'PRIMARY KEY': '(timestamp, ven_id)',
        },
      )
    except DatabaseError as e:
      logger.error(f'Failed to initialize database: {e}')
      raise

  def convert_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    """
    Generate a load profiler DataFrame from the given data

    Args:
        data (List[Dict[str, Any]]): List of intervals with dtstart and signal_payload

    Returns:
        pd.DataFrame: Transformed load profiler DataFrame
    """
    if not data:
      return {
        'dstart': np.array([]),
        'duration': np.array([]),
        'signal_payload': np.array([]),
      }

    dstart = np.array(
      [int(interval['dtstart'].timestamp() * 1000) for interval in data]
    )
    duration = np.array(
      [int(interval['duration'].total_seconds() * 1000) for interval in data]
    )
    signal_payload = np.array([interval['signal_payload'] for interval in data])

    sort_idx = np.argsort(dstart)
    return {
      'dstart': dstart[sort_idx],
      'duration': duration[sort_idx],
      'signal_payload': signal_payload[sort_idx],
    }

  def insert_load_profile(
    self, data: List[Dict[str, Any]]
  ) -> Dict[str, int | List[Any]]:
    """
    Insert the load profiler data into the database using batch processing.

    Args:
        data (List[Dict[str, Any]]): List of dictionaries containing load profiler data
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
        except (ValueError, KeyError, TypeError) as e:
          results['failed'] += 1
          results['errors'].append({'data': interval, 'error': str(e)})
          logger.error(f'Failed to process record: {str(e)}')
          continue

      if batch_values:
        try:
          self.db_manager.insert_values_batch(
            table_name='load_profiles',
            columns=['dstart', 'duration', 'signal_payload'],
            conflict_cols=['dstart'],
            batch_values=batch_values,
            # replace=True,
          )
          results['success'] += len(batch_values)
        except DatabaseError as e:
          results['failed'] += len(batch_values)
          results['errors'].append({'batch': batch_values, 'error': str(e)})
          logger.error(f'Failed to insert batch: {str(e)}')

    logger.info(
      f'Insertion complete. Succeeded: {results["success"]}, Failed: {results["failed"]}'
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
        conflict_cols=['timestamp'],
        # replace=True,
        # batch_size=self.batch_size,  # Adjust this value based on your needs
      )

      logger.info(f'Successfully inserted {len(data)} consumption records')

    except (DatabaseError, KeyError) as e:
      logger.error(f'Failed to insert consumption batch: {str(e)}')
      raise

  def get_latest_resource_consumption(
    self,
    target_timestamp: int,
    resource_id: str,
    time_window_ms: int = 15 * 60 * 1000,  # Default 15 minutes in milliseconds
  ) -> float:
    """
    Get the latest consumption value for a specific resource within the specified time window.

    Args:
        target_timestamp (int): The target timestamp in milliseconds to search from
        resource_id (str): The identifier of the resource to query
        time_window_ms (int): The time window in milliseconds to look back (default: 15 minutes)

    Returns:
        float: The latest consumption value if found within the time window, 0 otherwise
    """
    try:
      query = """
              SELECT value
              FROM consumption
              WHERE resource_id = ?
              AND timestamp >= ? - ?
              AND timestamp <= ?
              ORDER BY timestamp DESC
              LIMIT 1
            """

      params = [resource_id, target_timestamp, time_window_ms, target_timestamp]
      rows = self.db_manager.execute_query(query, params)

      return float(rows[0]['value']) if rows else 0.0

    except DatabaseError as e:
      logger.error(
        f'Failed to retrieve latest consumption for resource {resource_id}: {str(e)}'
      )
      raise
    except Exception as e:
      logger.error(
        f'Unexpected error retrieving consumption for resource {resource_id}: {str(e)}'
      )
      return 0.0

  def get_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'dstart ASC',
  ) -> Dict[str, np.ndarray]:
    """
    Retrieve the load profiler data from the database with ordered pagination.

    Args:
        limit: Optional[int] - Maximum number of records to return
        offset: Optional[int] - Number of records to skip
        order_by: str - Column and direction to order by (default: 'dstart ASC')

    Returns:
        Dict[str, np.ndarray]: Load profiler data
    """
    allowed_columns = {'dstart', 'duration', 'signal_payload'}
    allowed_directions = {'ASC', 'DESC'}

    # Parse and validate order_by
    try:
      column, direction = order_by.split()
      if column not in allowed_columns or direction not in allowed_directions:
        raise ValueError('Invalid order_by clause')
    except ValueError:
      logger.error(f'Invalid order_by parameter: {order_by}')
      raise ValueError('Invalid order_by parameter')

    base_query = """
                      SELECT dstart, duration, signal_payload
                      FROM load_profiles
                      ORDER BY ? ?
                  """

    params = [column, direction]
    if limit is not None:
      base_query += ' LIMIT ?'
      params.append(limit)

    if offset is not None:
      base_query += ' OFFSET ?'
      params.append(offset)

    try:
      rows = self.db_manager.execute_query(base_query, tuple(params))
      if not rows:
        return {
          'dstart': np.array([]),
          'duration': np.array([]),
          'signal_payload': np.array([]),
        }

      columns = ['dstart', 'duration', 'signal_payload']
      rows_as_lists = [[d[col] for col in columns] for d in rows]
      data = list(zip(*rows_as_lists))
      return {
        'dstart': np.array(data[0], dtype=int),
        'duration': np.array(data[1], dtype=int),
        'signal_payload': np.array(data[2], dtype=float),
      }
    except DatabaseError as e:
      logger.error(f'Failed to retrieve load profiler data: {str(e)}')
      raise

  def insert_consumption(self, data: Dict[str, Any]) -> None:
    """
    Insert a single consumption record into the database.

    Args:
        data (Dict[str, Any]): Dictionary with consumption data.
    """
    self.insert_consumption_batch([data])

  def get_consumption(self) -> Dict[str, np.ndarray]:
    """
    Retrieve the consumption data from the database.

    Returns:
        Dict[str, np.ndarray]: Consumption data
    """
    query = 'SELECT timestamp, ven_id, resource_id, value FROM consumption'
    try:
      rows = self.db_manager.execute_query(query)
      if not rows:
        return {
          'timestamp': np.array([]),
          'ven_id': np.array([]),
          'resource_id': np.array([]),
          'value': np.array([]),
        }

      columns = ['timestamp', 'ven_id', 'resource_id', 'value']
      rows_as_lists = [[d[col] for col in columns] for d in rows]
      data = list(zip(*rows_as_lists))
      return {
        'timestamp': np.array(data[0]),
        'ven_id': np.array(data[1]),
        'resource_id': np.array(data[2]),
        'value': np.array(data[3]),
      }
    except DatabaseError as e:
      logger.error(f'Failed to retrieve consumption data: {str(e)}')
      raise

  def get_unique_vens(self) -> int:
    """
    Retrieve the number of unique VENs in the consumption data.

    Returns:
        int: Number of unique VENs
    """
    query = 'SELECT DISTINCT ven_id FROM consumption'
    rows = self.db_manager.execute_query(query)
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
    Retrieve the nearest consumption point for each unique combination of ven_id and resource_id
    to the given timestamp, considering only data points from the last 15 minutes.

    Args:
        target_timestamp (int): The target timestamp to search for.

    Returns:
        List[Dict[str, Any]]: A list of the nearest consumption point records for each unique
                             combination of ven_id and resource_id.
    """
    fifteen_minutes_ms = 15 * 60 * 1000
    query = """
        SELECT t1.timestamp, t1.ven_id, t1.resource_id, t1.value
        FROM consumption t1
        INNER JOIN (
            SELECT ven_id, resource_id, MIN(ABS(timestamp - ?)) AS min_diff
            FROM consumption
            WHERE timestamp >= ? - ?  -- Filter for last 15 minutes
            AND timestamp <= ?        -- up to target timestamp
            GROUP BY ven_id, resource_id  -- Group by both ven_id and resource_id
        ) t2
        ON t1.ven_id = t2.ven_id
        AND t1.resource_id = t2.resource_id  -- Join on both ven_id and resource_id
        AND ABS(t1.timestamp - ?) = t2.min_diff
        WHERE t1.timestamp >= ? - ?   -- Apply same filter to outer query
        AND t1.timestamp <= ?
    """
    params = [
      target_timestamp,  # For MIN(ABS(timestamp - ?))
      target_timestamp,  # For timestamp >= ? - ?
      fifteen_minutes_ms,  # The 15-minute window
      target_timestamp,  # For timestamp <= ?
      target_timestamp,  # For ABS(t1.timestamp - ?)
      target_timestamp,  # For outer WHERE timestamp >= ? - ?
      fifteen_minutes_ms,  # The 15-minute window again
      target_timestamp,  # For outer WHERE timestamp <= ?
    ]
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
        conflict_cols=['timestamp', 'ven_id'],
        batch_values=batch_values,
        # replace=True,
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
