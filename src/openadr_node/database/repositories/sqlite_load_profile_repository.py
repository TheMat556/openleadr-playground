from sqlite3 import DatabaseError
from typing import Dict, List, Any, Optional

import numpy as np
from injector import inject

from src.openadr_node import logger
from src.openadr_node.database.interfaces.services.idatabase_service import (
  IDatabaseService,
)
from src.openadr_node.database.interfaces.repositories.iload_profile_repository import (
  ILoadProfileRepository,
)


class SQLiteLoadProfileRepository(ILoadProfileRepository):
  @inject
  def __init__(self, db_service: IDatabaseService):
    self.db_service = db_service

  def save_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not data:
      return {'success': 0, 'failed': 0, 'errors': []}

    results = {'success': 0, 'failed': 0, 'errors': []}
    batch_values = []

    for interval in data:
      try:
        if not all(k in interval for k in ['dstart', 'duration', 'signal_payload']):
          raise ValueError(f'Missing required fields in record: {interval}')

        batch_values.append(
          [interval['dstart'], interval['duration'], interval['signal_payload']]
        )
      except (ValueError, KeyError) as e:
        results['failed'] += 1
        results['errors'].append({'data': interval, 'error': str(e)})
        continue

    if batch_values:
      try:
        query = """
                    INSERT OR REPLACE INTO load_profiles (dstart, duration, signal_payload)
                    VALUES (?, ?, ?)
                """
        self.db_service.execute_batch(query, batch_values)
        results['success'] = len(batch_values)
      except DatabaseError as e:
        results['failed'] += len(batch_values)
        results['errors'].append({'error': str(e)})

    return results

  def get_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'dstart ASC',
  ) -> Dict[str, np.ndarray]:
    query = (
      'SELECT dstart, duration, signal_payload FROM load_profiles ORDER BY ' + order_by
    )
    params = []

    if limit is not None:
      query += ' LIMIT ?'
      params.append(limit)
    if offset is not None:
      query += ' OFFSET ?'
      params.append(offset)

    try:
      rows = self.db_service.execute_query(query, params)
      if not rows:
        return {
          'dstart': np.array([]),
          'duration': np.array([]),
          'signal_payload': np.array([]),
        }

      return {
        'dstart': np.array([row['dstart'] for row in rows], dtype=int),
        'duration': np.array([row['duration'] for row in rows], dtype=int),
        'signal_payload': np.array(
          [row['signal_payload'] for row in rows], dtype=float
        ),
      }
    except DatabaseError as e:
      logger.error(f'Failed to retrieve load profile data: {str(e)}')
      raise

  def get_closest_point(self, target_timestamp: int) -> Optional[Dict[str, Any]]:
    query = """
            SELECT dstart, duration, signal_payload
            FROM load_profiles
            ORDER BY ABS(dstart - ?) ASC
            LIMIT 1
        """
    try:
      results = self.db_service.execute_query(query, [target_timestamp])
      return results[0] if results else None
    except DatabaseError as e:
      logger.error(f'Failed to get closest point: {str(e)}')
      raise
