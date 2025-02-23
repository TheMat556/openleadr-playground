from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlite3 import DatabaseError
import numpy as np
from numpy.typing import NDArray

from src.adr_node.database.domain.data.z_value_data import ZValueData
from src.adr_node.database.interfaces.repositories.iz_value_repository import (
  IZValueRepository,
)
from src.adr_node.database.interfaces.services.idatabase_service import IDatabaseService
import logging


class SQLiteZValueRepository(IZValueRepository):
  """
  Repository for managing z-values in SQLite database.

  Attributes
  ----------
  db_service : IDatabaseService
      The database service used for executing queries.
  """

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
      logging.error(f'Failed to create z-value record: {e}')
      raise

  def create_batch(self, entities: List[ZValueData]) -> List[ZValueData]:
    """
    Create or update multiple z-value records in a batch.
    Last updated: 2025-02-21 17:01:38 UTC by TheMat556
    """
    if not entities:
      return []

    query = """
        INSERT OR REPLACE INTO z_values (
            timestamp,
            ven_id,
            z_value
        )
        VALUES (?, ?, ?)
    """
    try:
      batch_values = [
        [entity.timestamp, entity.ven_id, entity.z_value] for entity in entities
      ]
      self.db_service.execute_batch(query, batch_values)
      return entities
    except DatabaseError as e:
      logging.error(
        f'Failed to create z-value batch at {datetime.now(timezone.utc).isoformat()}: {str(e)}'
      )
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
      logging.error(f'Failed to find z-values by timestamp range: {e}')
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
      logging.error(f'Failed to find z-values by VEN: {e}')
      raise

  def get_latest_z_values(
    self, time_window_ms: Optional[int] = None
  ) -> List[ZValueData]:
    """
    Modified to return all z-value records in the optional time window.
    """
    query = """
          SELECT timestamp, ven_id, z_value
          FROM z_values
      """
    params = []
    if time_window_ms is not None:
      current_time = int(datetime.utcnow().timestamp() * 1000)
      query += ' WHERE timestamp >= ?'
      params.append(current_time - time_window_ms)
    query += ' ORDER BY timestamp ASC'
    try:
      results = self.db_service.execute_query(query, params)
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logging.error(f'Failed to get latest z-values: {e}')
      raise

  def save_z_values(
    self, ven_ids: NDArray[np.str_], z_values: NDArray[np.float64], timestamp: int
  ) -> Dict[str, Any]:
    """
    Save or update z-values for multiple VENs.
    Last updated: 2025-02-21 16:55:54 UTC by TheMat556

    Parameters
    ----------
    ven_ids : NDArray[np.str_]
        Array of VEN IDs
    z_values : NDArray[np.float64]
        Array of z-values corresponding to VEN IDs
    timestamp : int
        Timestamp for the z-values

    Returns
    -------
    Dict[str, Any]
        Results of the save operation containing:
        - success: bool indicating if operation was successful
        - count: number of records processed
        - updated: number of records updated
        - inserted: number of records inserted
        - failed: number of failed operations
        - errors: list of error messages if any
    """
    if len(ven_ids) != len(z_values):
      raise ValueError('Length mismatch between ven_ids and z_values arrays')

    results = {
      'success': False,
      'count': 0,
      'updated': 0,
      'inserted': 0,
      'failed': 0,
      'errors': [],
    }

    try:
      # First check which records exist
      check_query = """
              SELECT ven_id
              FROM z_values
              WHERE timestamp = ? AND ven_id IN ({})
          """.format(','.join('?' * len(ven_ids)))

      check_params = [timestamp] + list(ven_ids)
      existing_records = self.db_service.execute_query(check_query, check_params)
      existing_ven_ids = {record['ven_id'] for record in existing_records}

      # Prepare batches for update and insert
      update_batch = []
      insert_batch = []

      for ven_id, z_value in zip(ven_ids, z_values):
        if ven_id in existing_ven_ids:
          update_batch.append(
            [float(z_value), datetime.now(timezone.utc), timestamp, str(ven_id)]
          )
        else:
          insert_batch.append(
            [
              timestamp,
              str(ven_id),
              float(z_value),
              datetime.now(timezone.utc),
              None,  # updated_at
            ]
          )

      # Execute updates
      if update_batch:
        update_query = """
                  UPDATE z_values
                  SET z_value = ?,
                      updated_at = ?
                  WHERE timestamp = ?
                  AND ven_id = ?
              """
        self.db_service.execute_batch(update_query, update_batch)
        results['updated'] = len(update_batch)

      # Execute inserts
      if insert_batch:
        insert_query = """
                  INSERT INTO z_values (
                      timestamp,
                      ven_id,
                      z_value,
                      created_at,
                      updated_at
                  )
                  VALUES (?, ?, ?, ?, ?)
              """
        self.db_service.execute_batch(insert_query, insert_batch)
        results['inserted'] = len(insert_batch)

      results['success'] = True
      results['count'] = results['updated'] + results['inserted']

    except Exception as e:
      results['failed'] = len(ven_ids)
      results['errors'].append(str(e))
      logging.error(
        f'Failed to save z-values at {datetime.now(timezone.utc).isoformat()}: {str(e)}'
      )

    return results

  def _map_to_domain(self, row: Dict[str, Any]) -> ZValueData:
    """Map database row to domain object."""
    return ZValueData(
      timestamp=row['timestamp'], ven_id=row['ven_id'], z_value=row['z_value']
    )

  def get_last_inserted_z_values(self, ven_ids: NDArray[np.str_]) -> List[ZValueData]:
    """
    Get the most recently inserted z-values for specified VEN IDs.
    Last updated: 2025-02-21 17:34:03 UTC by TheMat556
    """
    try:
      if len(ven_ids) == 0:
        return []

      query = """
              SELECT z1.timestamp, z1.ven_id, z1.z_value
              FROM z_values z1
              INNER JOIN (
                  SELECT ven_id, MAX(timestamp) as max_timestamp
                  FROM z_values
                  WHERE ven_id IN ({})
                  GROUP BY ven_id
              ) z2 ON z1.ven_id = z2.ven_id AND z1.timestamp = z2.max_timestamp
              ORDER BY z1.timestamp DESC
          """.format(','.join('?' * len(ven_ids)))

      results = self.db_service.execute_query(query, list(ven_ids))

      return [
        ZValueData(
          timestamp=row['timestamp'], ven_id=row['ven_id'], z_value=row['z_value']
        )
        for row in results
      ]

    except DatabaseError as e:
      logging.error(
        f'Failed to get last inserted z-values at {datetime.now(timezone.utc).isoformat()}: {str(e)}'
      )
      raise
