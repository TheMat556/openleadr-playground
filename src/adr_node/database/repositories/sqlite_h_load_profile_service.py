from datetime import datetime, timezone
from sqlite3 import DatabaseError
from typing import Dict, List, Any, Optional
import numpy as np
import logging

from src.adr_node.database.interfaces.repositories.ih_load_profile_repository import (
  IHLoadProfileRepository,
)
from src.adr_node.database.interfaces.services.idatabase_service import IDatabaseService


class SQLiteHLoadProfileRepository(IHLoadProfileRepository):
  """SQLite implementation of the IHLoadProfileRepository interface."""

  def __init__(self, db_service: IDatabaseService):
    self.db_service = db_service

  def save_h_load_profile(
    self, data: List[Dict[str, Any]], ven_id: Optional[str] = None
  ) -> Dict[str, Any]:
    """
    Save H-load profile data.

    Args:
        data: List of dictionaries containing timestamp and value
        ven_id: Optional VEN ID. If not provided, NULL will be used.

    Returns:
        Dictionary containing success/failure information
    """
    if not data:
      return {'success': 0, 'failed': 0, 'errors': []}

    results = {'success': 0, 'failed': 0, 'errors': []}
    batch_values = []

    for profile in data:
      try:
        if not all(k in profile for k in ['timestamp', 'value']):
          raise ValueError(f'Missing required fields in record: {profile}')

        batch_values.append(
          [profile['timestamp'], ven_id, profile['value']]  # Can be None
        )
      except (ValueError, KeyError) as e:
        results['failed'] += 1
        results['errors'].append({'data': profile, 'error': str(e)})
        continue

    if batch_values:
      try:
        query = """
                    INSERT OR REPLACE INTO h_load_profiles (timestamp, ven_id, value)
                    VALUES (?, ?, ?)
                """

        self.db_service.execute_batch(query, batch_values)
        results['success'] = len(batch_values)
      except DatabaseError as e:
        results['failed'] += len(batch_values)
        results['errors'].append({'error': str(e)})

    return results

  def get_h_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'timestamp ASC',
    ven_id: Optional[str] = None,
    timestamp: Optional[int] = None,
  ) -> Dict[str, np.ndarray]:
    """
    Retrieve H-load profile data.
    Last updated: 2025-02-21 16:05:30 UTC by TheMat556

    Args:
        limit: Optional limit on number of records
        offset: Optional offset for pagination
        order_by: SQL ORDER BY clause
        ven_id: Optional VEN ID to filter by
        timestamp: Optional timestamp to filter by

    Returns:
        Dictionary containing numpy arrays of timestamps, values, and ven_ids
    """
    query = """
            SELECT h.timestamp,
                   h.value,
                   h.ven_id
            FROM h_load_profiles h
            WHERE 1=1
        """
    params = []

    if ven_id is not None:
      query += ' AND h.ven_id = ?'
      params.append(ven_id)

    if timestamp is not None:
      query += ' AND h.timestamp = ?'
      params.append(timestamp)

    query += f' ORDER BY {order_by}'

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
          'timestamp': np.array([], dtype=int),
          'value': np.array([], dtype=float),
          'ven_ids': np.array([], dtype=str),
        }

      timestamps = []
      values = []
      ven_ids = []

      for row in rows:
        timestamps.append(row['timestamp'])
        values.append(row['value'])
        ven_ids.append(row['ven_id'])

      return {
        'timestamp': np.array(timestamps, dtype=int),
        'value': np.array(values, dtype=float),
        'ven_ids': np.array(ven_ids, dtype=str),
      }

    except DatabaseError as e:
      logging.error(
        f'Failed to retrieve h-load profile data at {datetime.now(timezone.utc).isoformat()}: {str(e)}'
      )
      raise

  def get_current_h_load_profile(
    self, ven_id: Optional[str] = None
  ) -> Optional[Dict[str, Any]]:
    """
    Get the most recent H-load profile value.

    Args:
        ven_id: Optional VEN ID to filter by

    Returns:
        Dictionary containing timestamp and value, or None if no data exists
    """
    query = """
            SELECT timestamp, ven_id, value
            FROM h_load_profiles
        """
    params = []

    if ven_id is not None:
      query += ' WHERE ven_id = ?'
      params.append(ven_id)

    query += ' ORDER BY timestamp DESC LIMIT 1'

    try:
      results = self.db_service.execute_query(query, params)
      return results[0] if results else None
    except DatabaseError as e:
      logging.error(f'Failed to get current h-load profile: {str(e)}')
      raise
