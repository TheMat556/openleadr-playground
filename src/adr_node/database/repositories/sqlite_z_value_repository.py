from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlite3 import DatabaseError
import numpy as np
from numpy.typing import NDArray

from src.adr_node.database.domain.data.z_value_data import ZValueData
from src.adr_node.database.interfaces.repositories.iz_value_repository import (
  IZValueRepository,
)
from src.adr_node.database.interfaces.services.idatabase_service import IDatabaseService
from src.openadr_node import logger


class SQLiteZValueRepository(IZValueRepository):
  """Repository for managing z-values in SQLite database."""

  def __init__(self, db_service: IDatabaseService):
    self.db_service = db_service

  def create(self, entity: ZValueData) -> ZValueData:
    """Create a single z-value record."""
    query = """
            INSERT INTO z_values (timestamp, ven_id, z_value)
            VALUES (?, ?, ?)
        """
    try:
      values = [entity.timestamp, entity.ven_id, entity.z_value]
      self.db_service.execute_query(query, values)
      return entity
    except DatabaseError as e:
      logger.error(f'Failed to create z-value record: {e}')
      raise

  def create_batch(self, entities: List[ZValueData]) -> List[ZValueData]:
    """Create multiple z-value records in a batch."""
    if not entities:
      return []

    query = """
            INSERT INTO z_values (timestamp, ven_id, z_value)
            VALUES (?, ?, ?)
        """
    try:
      batch_values = [
        [entity.timestamp, entity.ven_id, entity.z_value] for entity in entities
      ]
      self.db_service.execute_batch(query, batch_values)
      return entities
    except DatabaseError as e:
      logger.error(f'Failed to create z-value batch: {e}')
      raise

  def find_by_timestamp_range(
    self, start_timestamp: int, end_timestamp: int
  ) -> List[ZValueData]:
    """Find z-values within a timestamp range."""
    query = """
            SELECT timestamp, ven_id, z_value
            FROM z_values
            WHERE timestamp BETWEEN ? AND ?
            ORDER BY timestamp ASC
        """
    try:
      results = self.db_service.execute_query(query, [start_timestamp, end_timestamp])
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to find z-values by timestamp range: {e}')
      raise

  def find_by_ven(self, ven_id: str, limit: int = 100) -> List[ZValueData]:
    """Find z-values for a specific VEN."""
    query = """
            SELECT timestamp, ven_id, z_value
            FROM z_values
            WHERE ven_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
    try:
      results = self.db_service.execute_query(query, [ven_id, limit])
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to find z-values by VEN: {e}')
      raise

  def get_latest_z_values(
    self, time_window_ms: Optional[int] = None
  ) -> List[ZValueData]:
    """Get the latest z-values for each VEN within optional time window."""
    base_query = """
            SELECT t1.timestamp, t1.ven_id, t1.z_value
            FROM z_values t1
            INNER JOIN (
                SELECT ven_id, MAX(timestamp) as max_timestamp
                FROM z_values
                {where_clause}
                GROUP BY ven_id
            ) t2 ON t1.ven_id = t2.ven_id AND t1.timestamp = t2.max_timestamp
        """

    params = []
    where_clause = ''

    if time_window_ms is not None:
      current_time = int(datetime.utcnow().timestamp() * 1000)
      where_clause = 'WHERE timestamp >= ?'
      params.append(current_time - time_window_ms)

    query = base_query.format(where_clause=where_clause)

    try:
      results = self.db_service.execute_query(query, params)
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to get latest z-values: {e}')
      raise

  def save_z_values(
    self, ven_ids: NDArray[np.str_], z_values: NDArray[np.float64], timestamp: int
  ) -> Dict[str, Any]:
    """Save z-values for multiple VENs."""
    if len(ven_ids) != len(z_values):
      raise ValueError('Length mismatch between ven_ids and z_values arrays')

    results = {'success': False, 'failed': 0, 'errors': []}

    try:
      query = """
                INSERT INTO z_values (timestamp, ven_id, z_value)
                VALUES (?, ?, ?)
            """

      batch_values = [
        [timestamp, str(ven_id), float(z_value)]
        for ven_id, z_value in zip(ven_ids, z_values)
      ]

      self.db_service.execute_batch(query, batch_values)
      results['success'] = True
      results['count'] = len(batch_values)

    except Exception as e:
      results['failed'] = len(ven_ids)
      results['errors'].append(str(e))
      logger.error(f'Failed to save z-values: {e}')

    return results

  def _map_to_domain(self, row: Dict[str, Any]) -> ZValueData:
    """Map database row to domain object."""
    return ZValueData(
      timestamp=row['timestamp'], ven_id=row['ven_id'], z_value=row['z_value']
    )
