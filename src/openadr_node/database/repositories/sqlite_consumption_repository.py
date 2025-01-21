from sqlite3 import DatabaseError
from typing import Dict, List, Any

import numpy as np

from src.openadr_node import logger
from src.openadr_node.database.interfaces.repositories.iconsumption_repository import (
  IConsumptionRepository,
)
from src.openadr_node.database.interfaces.services.idatabase_service import (
  IDatabaseService,
)


class SQLiteConsumptionRepository(IConsumptionRepository):
  def __init__(self, db_service: IDatabaseService):
    self.db_service = db_service

  def save_consumption_batch(self, data: List[Dict[str, Any]]) -> None:
    if not data:
      logger.warning('No consumption data provided for insertion')
      return

    try:
      batch_values = [
        [record['timestamp'], record['ven_id'], record['resource_id'], record['value']]
        for record in data
      ]

      query = """
                INSERT OR REPLACE INTO consumption
                (timestamp, ven_id, resource_id, value)
                VALUES (?, ?, ?, ?)
            """
      self.db_service.execute_batch(query, batch_values)
      logger.info(f'Successfully inserted {len(data)} consumption records')
    except (DatabaseError, KeyError) as e:
      logger.error(f'Failed to insert consumption batch: {str(e)}')
      raise

  def get_consumption(self) -> Dict[str, np.ndarray]:
    query = 'SELECT timestamp, ven_id, resource_id, value FROM consumption'
    try:
      rows = self.db_service.execute_query(query)
      if not rows:
        return {
          'timestamp': np.array([]),
          'ven_id': np.array([]),
          'resource_id': np.array([]),
          'value': np.array([]),
        }

      return {
        'timestamp': np.array([row['timestamp'] for row in rows]),
        'ven_id': np.array([row['ven_id'] for row in rows]),
        'resource_id': np.array([row['resource_id'] for row in rows]),
        'value': np.array([row['value'] for row in rows]),
      }
    except DatabaseError as e:
      logger.error(f'Failed to retrieve consumption data: {str(e)}')
      raise

  def get_closest_consumption_points(
    self, target_timestamp: int
  ) -> List[Dict[str, Any]]:
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
    try:
      return self.db_service.execute_query(query, [target_timestamp, target_timestamp])
    except DatabaseError as e:
      logger.error(f'Failed to get closest consumption points: {str(e)}')
      raise

  def get_unique_vens(self) -> int:
    query = 'SELECT COUNT(DISTINCT ven_id) as count FROM consumption'
    try:
      result = self.db_service.execute_query(query)
      return result[0]['count'] if result else 0
    except DatabaseError as e:
      logger.error(f'Failed to get unique VENs count: {str(e)}')
      raise
