from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlite3 import DatabaseError

from src.adr_node.database.domain.data.consumption_data import ConsumptionData
from src.adr_node.database.domain.query.consumption_query import ConsumptionQuery
from src.adr_node.database.interfaces.repositories.iconsumption_repository import (
  IConsumptionRepository,
)
from src.adr_node.database.interfaces.services.idatabase_service import IDatabaseService
from src.openadr_node import logger


class SQLiteConsumptionRepository(IConsumptionRepository):
  def __init__(self, db_service: IDatabaseService):
    self.db_service = db_service

  def _map_to_domain(self, row: Dict[str, Any]) -> ConsumptionData:
    return ConsumptionData(
      timestamp=row['timestamp'],
      ven_id=row['ven_id'],
      resource_id=row['resource_id'],
      value=row['value'],
      created_at=row['created_at'],
      updated_at=row['updated_at'] if row.get('updated_at') else None,
      report_type=row['report_type'],
      reading_type=row['reading_type'],
    )

  # Base Repository Methods (CRUD)
  def create(self, entity: ConsumptionData) -> ConsumptionData:
    query = """
                INSERT INTO consumption
                (timestamp, ven_id, resource_id, value, created_at, report_type, reading_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
    try:
      values = [
        entity.timestamp,
        entity.ven_id,
        entity.resource_id,
        entity.value,
        entity.created_at,
        entity.report_type,
        entity.reading_type,
      ]
      self.db_service.execute_query(query, values)
      return entity
    except DatabaseError as e:
      logger.error(f'Failed to create consumption record: {e}')
      raise

  def create_batch(self, entities: List[ConsumptionData]) -> List[ConsumptionData]:
    if not entities:
      return []

    query = """
                INSERT INTO consumption
                (timestamp, ven_id, resource_id, value, created_at, report_type, reading_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
    try:
      batch_values = [
        [
          entity.timestamp,
          entity.ven_id,
          entity.resource_id,
          entity.value,
          entity.created_at.isoformat(),
          entity.report_type,
          entity.reading_type,
        ]
        for entity in entities
      ]
      self.db_service.execute_batch(query, batch_values)
      return entities
    except DatabaseError as e:
      logger.error(f'Failed to create consumption batch: {e}')
      raise

  def read(self, id: Any) -> Optional[ConsumptionData]:
    query = 'SELECT * FROM consumption WHERE id = ?'
    try:
      result = self.db_service.execute_query(query, [id])
      return self._map_to_domain(result[0]) if result else None
    except DatabaseError as e:
      logger.error(f'Failed to read consumption record: {e}')
      raise

  def read_all(self, query: Optional[ConsumptionQuery] = None) -> List[ConsumptionData]:
    base_query = 'SELECT * FROM consumption'
    params = []
    where_clauses = []

    if query:
      if query.timestamp_start:
        where_clauses.append('timestamp >= ?')
        params.append(query.timestamp_start)
      if query.timestamp_end:
        where_clauses.append('timestamp <= ?')
        params.append(query.timestamp_end)
      if query.ven_id:
        where_clauses.append('ven_id = ?')
        params.append(query.ven_id)
      if query.resource_id:
        where_clauses.append('resource_id = ?')
        params.append(query.resource_id)

      if where_clauses:
        base_query += f' WHERE {" AND ".join(where_clauses)}'

      base_query += f' ORDER BY {query.order_by} {query.order_direction}'
      base_query += ' LIMIT ? OFFSET ?'
      params.extend([query.limit, query.offset])

    try:
      results = self.db_service.execute_query(base_query, params)
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to read consumption records: {e}')
      raise

  def update(self, entity: ConsumptionData) -> ConsumptionData:
    query = """
                UPDATE consumption
                SET timestamp = ?, ven_id = ?, resource_id = ?, value = ?, updated_at = ?, report_type = ?, reading_type = ?
                WHERE id = ?
            """
    try:
      values = [
        entity.timestamp,
        entity.ven_id,
        entity.resource_id,
        entity.value,
        datetime.utcnow().isoformat(),
        entity.report_type,
        entity.reading_type,
        entity.id,
      ]
      self.db_service.execute_query(query, values)
      return entity
    except DatabaseError as e:
      logger.error(f'Failed to update consumption record: {e}')
      raise

  def update_batch(self, entities: List[ConsumptionData]) -> List[ConsumptionData]:
    query = """
                UPDATE consumption
                SET timestamp = ?, ven_id = ?, resource_id = ?, value = ?, updated_at = ?, report_type = ?, reading_type = ?
                WHERE id = ?
            """
    try:
      current_time = datetime.utcnow().isoformat()
      batch_values = [
        [
          entity.timestamp,
          entity.ven_id,
          entity.resource_id,
          entity.value,
          current_time,
          entity.report_type,
          entity.reading_type,
          entity.id,
        ]
        for entity in entities
      ]
      self.db_service.execute_batch(query, batch_values)
      return entities
    except DatabaseError as e:
      logger.error(f'Failed to update consumption batch: {e}')
      raise

  def delete(self, id: Any) -> bool:
    query = 'DELETE FROM consumption WHERE id = ?'
    try:
      self.db_service.execute_query(query, [id])
      return True
    except DatabaseError as e:
      logger.error(f'Failed to delete consumption record: {e}')
      raise

  def delete_batch(self, ids: List[Any]) -> bool:
    if not ids:
      return True

    placeholders = ','.join(['?' for _ in ids])
    query = f'DELETE FROM consumption WHERE id IN ({placeholders})'
    try:
      self.db_service.execute_query(query, ids)
      return True
    except DatabaseError as e:
      logger.error(f'Failed to delete consumption batch: {e}')
      raise

  # Consumption-specific methods
  def find_by_timestamp_range(
    self, start_timestamp: int, end_timestamp: int
  ) -> List[ConsumptionData]:
    query = """
                SELECT * FROM consumption
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """
    try:
      results = self.db_service.execute_query(query, [start_timestamp, end_timestamp])
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to find consumption by timestamp range: {e}')
      raise

  def find_by_ven(self, ven_id: str, limit: int = 100) -> List[ConsumptionData]:
    query = """
                SELECT * FROM consumption
                WHERE ven_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
    try:
      results = self.db_service.execute_query(query, [ven_id, limit])
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to find consumption by VEN: {e}')
      raise

  def find_by_resource(
    self, resource_id: str, limit: int = 100
  ) -> List[ConsumptionData]:
    query = """
                SELECT * FROM consumption
                WHERE resource_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
    try:
      results = self.db_service.execute_query(query, [resource_id, limit])
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to find consumption by resource: {e}')
      raise

  def find_nearest_to_timestamp(
    self, timestamp: int, max_distance: Optional[int] = None
  ) -> Optional[ConsumptionData]:
    query = """
                SELECT *, ABS(timestamp - ?) as distance
                FROM consumption
                WHERE 1=1
                {max_distance_clause}
                ORDER BY distance ASC
                LIMIT 1
            """
    params = [timestamp]

    max_distance_clause = ''
    if max_distance:
      max_distance_clause = 'AND ABS(timestamp - ?) <= ?'
      params.extend([timestamp, max_distance])

    query = query.format(max_distance_clause=max_distance_clause)
    try:
      results = self.db_service.execute_query(query, params)
      return self._map_to_domain(results[0]) if results else None
    except DatabaseError as e:
      logger.error(f'Failed to find nearest consumption: {e}')
      raise

  def count_unique_vens(self) -> int:
    query = 'SELECT COUNT(DISTINCT ven_id) as count FROM consumption'
    try:
      result = self.db_service.execute_query(query)
      return result[0]['count'] if result else 0
    except DatabaseError as e:
      logger.error(f'Failed to count unique VENs: {e}')
      raise

  def get_latest_readings(self, limit: int = 10) -> List[ConsumptionData]:
    query = """
                SELECT * FROM consumption
                ORDER BY timestamp DESC
                LIMIT ?
            """
    try:
      results = self.db_service.execute_query(query, [limit])
      return [self._map_to_domain(row) for row in results]
    except DatabaseError as e:
      logger.error(f'Failed to get latest readings: {e}')
      raise

  def find_closest_consumption_points(
    self, target_timestamp: int, time_window_ms: Optional[int] = None
  ) -> List[ConsumptionData]:
    """
    Retrieve the latest consumption point for each unique VEN ID within the time window.

    Args:
        target_timestamp (int): The target timestamp to search around
        time_window_ms (Optional[int]): Optional time window in milliseconds to limit the search

    Returns:
        List[ConsumptionData]: List of latest consumption points for each VEN
    """
    try:
      # First, check if we have any data at all
      check_query = 'SELECT COUNT(*) as count FROM consumption'
      total_count = self.db_service.execute_query(check_query, [])[0]['count']
      logger.info(f'Total records in consumption table: {total_count}')

      # Build the main query
      base_query = """
              SELECT t1.*
              FROM consumption t1
              INNER JOIN (
                  SELECT ven_id,
                         MAX(timestamp) AS latest_timestamp
                  FROM consumption
                  {where_clause}
                  GROUP BY ven_id
              ) t2
              ON t1.ven_id = t2.ven_id
              AND t1.timestamp = t2.latest_timestamp
              ORDER BY t1.ven_id
          """

      params = []
      where_clause = ''

      if time_window_ms is not None:
        window_start = target_timestamp - time_window_ms
        window_end = target_timestamp + time_window_ms

        where_clause = """
                  WHERE timestamp >= ? AND timestamp <= ?
              """
        params.extend([window_start, window_end])

        # Log the time window details
        logger.info(
          f'Searching in window: '
          f'start={datetime.fromtimestamp(window_start).strftime("%Y-%m-%d %H:%M:%S")} '
          f'end={datetime.fromtimestamp(window_end).strftime("%Y-%m-%d %H:%M:%S")} '
          f'target={datetime.fromtimestamp(target_timestamp).strftime("%Y-%m-%d %H:%M:%S")}'
        )

        # Check how many records are in the time window
        window_check_query = """
                  SELECT COUNT(*) as count
                  FROM consumption
                  WHERE timestamp >= ? AND timestamp <= ?
              """
        window_count = self.db_service.execute_query(
          window_check_query, [window_start, window_end]
        )[0]['count']
        logger.info(f'Records in time window: {window_count}')

      query = base_query.format(where_clause=where_clause)
      logger.debug(f'Executing query: {query} with params: {params}')

      results = self.db_service.execute_query(query, params)

      if not results:
        logger.warning(
          f'No consumption points found. '
          f'Target timestamp: {datetime.fromtimestamp(target_timestamp).strftime("%Y-%m-%d %H:%M:%S")}, '
          f'Window size: {time_window_ms / 1000 if time_window_ms else "None"} seconds'
        )
        return []

      consumption_points = [self._map_to_domain(row) for row in results]
      logger.info(f'Found {len(consumption_points)} consumption points')

      # Log the timestamps of found points
      for point in consumption_points:
        logger.debug(
          f'Point found - VEN: {point.ven_id}, '
          f'Timestamp: {datetime.fromtimestamp(point.timestamp).strftime("%Y-%m-%d %H:%M:%S")}, '
          f'Value: {point.value}'
        )

      return consumption_points

    except DatabaseError as e:
      logger.error(
        f'Database error while finding consumption points: {str(e)}\n'
        f'Target timestamp: {datetime.fromtimestamp(target_timestamp).strftime("%Y-%m-%d %H:%M:%S")}'
      )
      raise
    except Exception as e:
      logger.error(
        f'Unexpected error while finding consumption points: {str(e)}\n'
        f'Target timestamp: {datetime.fromtimestamp(target_timestamp).strftime("%Y-%m-%d %H:%M:%S")}'
      )
      raise

  def find_closest_consumption_for_ven(
    self, target_timestamp: int, ven_id: str, time_window_ms: Optional[int] = None
  ) -> Optional[ConsumptionData]:
    """
    Find the closest consumption point for a specific VEN ID near the target timestamp.

    Args:
        target_timestamp (int): The target timestamp to search for
        ven_id (str): The VEN ID to search for
        time_window_ms (Optional[int]): Optional time window in milliseconds to limit the search

    Returns:
        Optional[ConsumptionData]: The nearest consumption point or None if not found
    """
    base_query = """
                SELECT *,
                       ABS(timestamp - ?) as distance
                FROM consumption
                WHERE ven_id = ?
                {time_window_clause}
                ORDER BY distance ASC
                LIMIT 1
            """

    params = [target_timestamp, ven_id]
    time_window_clause = ''

    if time_window_ms is not None:
      time_window_clause = """
                    AND timestamp >= ? - ?
                    AND timestamp <= ? + ?
                """
      params.extend(
        [target_timestamp, time_window_ms, target_timestamp, time_window_ms]
      )

    query = base_query.format(time_window_clause=time_window_clause)

    try:
      results = self.db_service.execute_query(query, params)
      if not results:
        return None

      return self._map_to_domain(results[0])
    except DatabaseError as e:
      logger.error(
        f'Failed to find closest consumption for VEN {ven_id} at timestamp {target_timestamp}: {e}'
      )
      raise
