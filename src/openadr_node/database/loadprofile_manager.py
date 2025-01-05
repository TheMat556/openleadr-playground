import logging
from typing import List, Dict, Any, Optional
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

  def insert_load_profile(self, data: List[Dict[str, Any]]) -> dict[
                                                                 str, int | list[Any]] | \
                                                               dict[
                                                                 str, int | list[Any]]:
    """
    Insert the load profile data into the database using batch processing.

    Args:
        data (List[Dict[str, Any]]): List of dictionaries containing load profile data
            with 'dstart', 'duration', and 'signal_payload' keys.
    """
    if not data:
      logger.warning('No data provided for insertion')
      return {"success": 0, "failed": 0, "errors": []}

    results = {"success": 0, "failed": 0, "errors": []}

    for i in range(0, len(data), self.batch_size):
      batch = data[i:i + self.batch_size]
      batch_values = []

      for interval in batch:
        try:
          # Validate data before adding to batch
          if not all(k in interval for k in ['dstart', 'duration', 'signal_payload']):
            raise ValueError(f"Missing required fields in record: {interval}")

          batch_values.append([
            interval['dstart'],
            interval['duration'],
            interval['signal_payload']
          ])
        except Exception as e:
          results["failed"] += 1
          results["errors"].append({"data": interval, "error": str(e)})
          logger.error(f"Failed to process record: {str(e)}")
          continue

      if batch_values:
        try:
          self.db_manager.insert_values_batch(
            table_name='load_profiles',
            columns=['dstart', 'duration', 'signal_payload'],
            batch_values=batch_values,
            replace=True
          )
          results["success"] += len(batch_values)
        except DatabaseError as e:
          results["failed"] += len(batch_values)
          results["errors"].append({"batch": batch_values, "error": str(e)})
          logger.error(f"Failed to insert batch: {str(e)}")

    logger.info(
      f"Insertion complete. Succeeded: {results['success']}, Failed: {results['failed']}")
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
    order_by: str = 'dstart ASC'
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
    query = '''
            SELECT dstart, duration, signal_payload
            FROM load_profiles
            ORDER BY {}
        '''.format(order_by)

    if limit is not None:
      query += f' LIMIT {limit}'

    if offset is not None:
      query += f' OFFSET {offset}'

    try:
      rows = self.db_manager.execute_query(query)
      df = pd.DataFrame(rows)

      if not df.empty:
        df.set_index('dstart', inplace=True)
      return df
    except DatabaseError as e:
      logger.error(f"Failed to retrieve load profile data: {str(e)}")
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
