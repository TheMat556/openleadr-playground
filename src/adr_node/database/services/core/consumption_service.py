import time
from datetime import datetime
from typing import List, Optional

from src.adr_node.database.domain.results.consumption_batch_result import (
  ConsumptionBatchResult,
)
from src.adr_node.database.domain.data.consumption_data import ConsumptionData
from src.adr_node.database.domain.query.consumption_query import ConsumptionQuery
from src.adr_node.database.interfaces.repositories.iconsumption_repository import (
  IConsumptionRepository,
)
from src.adr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.adr_node.database.domain.results.consumption_service_result import (
  ConsumptionServiceResult,
)
from src.openadr_node import logger


class ConsumptionService(IConsumptionService):
  def __init__(self, repository: IConsumptionRepository):
    self.repository = repository

  def create_consumption_record(
    self, data: ConsumptionData
  ) -> ConsumptionServiceResult:
    try:
      self._validate_consumption_data(data)
      result = self.repository.create(data)
      return ConsumptionServiceResult(success=True, data=result)
    except Exception as e:
      logger.error(f'Failed to create consumption record: {str(e)}')
      return ConsumptionServiceResult(success=False, error=str(e))

  def create_consumption_batch(
    self, data: List[ConsumptionData]
  ) -> ConsumptionBatchResult:
    if not data:
      return ConsumptionBatchResult(
        successful_records=0, failed_records=0, errors=['No data provided']
      )

    successful = []
    errors = []

    for record in data:
      try:
        self._validate_consumption_data(record)
        successful.append(record)
      except ValueError as e:
        errors.append(f'Validation error for record: {str(e)}')

    if successful:
      try:
        self.repository.create_batch(successful)
      except Exception as e:
        return ConsumptionBatchResult(
          successful_records=0,
          failed_records=len(data),
          errors=[f'Batch insertion failed: {str(e)}'],
        )

    return ConsumptionBatchResult(
      successful_records=len(successful),
      failed_records=len(data) - len(successful),
      errors=errors,
    )

  def find_consumption_by_id(self, consumption_id: int) -> ConsumptionServiceResult:
    try:
      result = self.repository.read(consumption_id)
      return ConsumptionServiceResult(success=bool(result), data=result)
    except Exception as e:
      logger.error(f'Failed to find consumption by ID: {str(e)}')
      return ConsumptionServiceResult(success=False, error=str(e))

  def find_active_consumption(self, timestamp: int) -> ConsumptionServiceResult:
    try:
      query = ConsumptionQuery(
        timestamp_start=timestamp, timestamp_end=timestamp, limit=1
      )
      result = self.repository.read_all(query)

      if not result:
        return ConsumptionServiceResult(
          success=False, error='No active consumption found'
        )

      total_value = sum(record.value for record in result)
      return ConsumptionServiceResult(
        success=True,
        data={
          'timestamp': timestamp,
          'total_value': total_value,
          'unit': 'kWh',
          'records': result,
        },
      )
    except Exception as e:
      logger.error(f'Failed to find active consumption: {str(e)}')
      return ConsumptionServiceResult(success=False, error=str(e))

  def find_consumption_by_criteria(
    self, query: ConsumptionQuery
  ) -> ConsumptionServiceResult:
    try:
      result = self.repository.read_all(query)
      return ConsumptionServiceResult(success=True, data=result)
    except Exception as e:
      logger.error(f'Failed to find consumption by criteria: {str(e)}')
      return ConsumptionServiceResult(success=False, error=str(e))

  def find_nearest_consumption(
    self, timestamp: int, max_distance: Optional[int] = None
  ) -> ConsumptionServiceResult:
    try:
      result = self.repository.find_nearest_to_timestamp(timestamp, max_distance)
      return ConsumptionServiceResult(success=bool(result), data=result)
    except Exception as e:
      logger.error(f'Failed to find nearest consumption: {str(e)}')
      return ConsumptionServiceResult(success=False, error=str(e))

  def get_ven_statistics(self) -> ConsumptionServiceResult:
    try:
      ven_count = self.repository.count_unique_vens()
      latest_readings = self.repository.get_latest_readings(limit=5)

      return ConsumptionServiceResult(
        success=True,
        data={
          'total_vens': ven_count,
          'latest_readings': latest_readings,
          'timestamp': datetime.utcnow(),
        },
      )
    except Exception as e:
      logger.error(f'Failed to get VEN statistics: {str(e)}')
      return ConsumptionServiceResult(success=False, error=str(e))

  def _validate_consumption_data(self, data: ConsumptionData) -> None:
    """Validate consumption data before processing."""
    if not data.ven_id:
      raise ValueError('VEN ID is required')
    if not data.resource_id:
      raise ValueError('Resource ID is required')
    if data.value < 0:
      raise ValueError('Consumption value cannot be negative')
    if not data.timestamp:
      raise ValueError('Timestamp is required')

  def get_closest_consumption_points(
    self, target_timestamp: int, time_window_ms: int = 15 * 60 * 1000
  ) -> ConsumptionServiceResult:
    try:
      points = self.repository.find_closest_consumption_points(
        target_timestamp, time_window_ms
      )

      if not points:
        return ConsumptionServiceResult(
          success=False,
          error='No consumption points found',
          timestamp=datetime.utcnow(),
        )

      total_value = sum(point.value for point in points)

      tst = ConsumptionServiceResult(
        success=True,
        data={
          'timestamp': target_timestamp,
          'consumption_points': points,
          'overall_value': total_value,
          'unit': 'kWh',
          'ven_count': len(points),
        },
        timestamp=datetime.utcnow(),
      )

      return tst

    except Exception as e:
      logger.error(f'Failed to get closest consumption points: {str(e)}')
      return ConsumptionServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )

  def get_closest_consumption_point(
    self, timestamp: int, ven_id: str, resource_id: str
  ) -> ConsumptionServiceResult:
    """
    Get the closest consumption point for a specific VEN and resource.

    Args:
        timestamp (int): Target timestamp
        ven_id (str): VEN identifier
        resource_id (str): Resource identifier

    Returns:
        ConsumptionServiceResult: Contains consumption data or error information
    """
    try:
      consumption_point = self.repository.find_closest_consumption_for_ven(
        target_timestamp=timestamp, ven_id=ven_id
      )

      if not consumption_point:
        return ConsumptionServiceResult(
          success=False,
          error=f'No consumption point found for VEN {ven_id}',
          timestamp=datetime.utcnow(),
        )

      return ConsumptionServiceResult(
        success=True,
        data={
          'timestamp': consumption_point.timestamp,
          'ven_id': consumption_point.ven_id,
          'resource_id': consumption_point.resource_id,
          'value': consumption_point.value,
          'unit': 'kWh',
        },
        timestamp=datetime.utcnow(),
      )

    except Exception as e:
      logger.error(f'Failed to get closest consumption point: {str(e)}')
      return ConsumptionServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )

  def get_current_consumption(self) -> ConsumptionServiceResult:
    """
    Get the current consumption by aggregating values from the last 15 minutes.
    Uses get_closest_consumption_points internally with a 15-minute window.

    Returns:
        ConsumptionServiceResult: Contains the aggregated consumption data with:
            - total_consumption: sum of all consumption values
            - average_consumption: average consumption per point
            - point_count: number of consumption points
            - timestamp_range: start and end timestamps of the window
            - unit: measurement unit (kWh)
    """
    try:
      current_timestamp = int(datetime.utcnow().timestamp())
      window_ms = 15 * 60 * 1000  # 15 minutes in milliseconds

      result = self.get_closest_consumption_points(
        target_timestamp=current_timestamp, time_window_ms=window_ms
      )

      if not result.success:
        return ConsumptionServiceResult(
          success=False,
          error=f'Failed to get current consumption: {result.error}',
          timestamp=datetime.utcnow(),
        )

      points = result.data.get('consumption_points', [])

      if not points:
        return ConsumptionServiceResult(
          success=False,
          error='No consumption points found in the last 15 minutes',
          timestamp=datetime.utcnow(),
        )

      total_consumption = result.data['overall_value']
      point_count = len(points)
      average_consumption = total_consumption / point_count if point_count > 0 else 0

      timestamps = [point.timestamp for point in points]
      start_timestamp = min(timestamps)
      end_timestamp = max(timestamps)

      return ConsumptionServiceResult(
        success=True,
        data={
          'total_consumption': total_consumption,
          'average_consumption': average_consumption,
          'point_count': point_count,
          'timestamp_range': {
            'start': start_timestamp,
            'end': end_timestamp,
            'window_ms': window_ms,
          },
          'unit': 'kWh',
        },
        timestamp=datetime.utcnow(),
      )

    except Exception as e:
      logger.error(f'Failed to calculate current consumption: {str(e)}')
      return ConsumptionServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )

  def get_vens_active_last_hour(self) -> ConsumptionServiceResult:
    """
    Retrieves all unique VEN IDs that have published data in the last hour.

    Returns:
        ConsumptionServiceResult: Contains a list of VEN IDs active within the last hour.
    """
    try:
      current_timestamp = int(time.time())
      print('current_timestamp', current_timestamp)
      one_hour_ago = current_timestamp - 3600
      print('one_hour_ago', one_hour_ago)

      # Retrieve consumption records from the last hour
      records = self.repository.find_by_timestamp_range(one_hour_ago, current_timestamp)

      if not records:
        return ConsumptionServiceResult(
          success=False,
          error='No records found in the last hour',
          timestamp=datetime.utcnow(),
        )

      unique_vens = {record.ven_id for record in records}
      return ConsumptionServiceResult(
        success=True,
        data={'active_vens': list(unique_vens)},
        timestamp=datetime.utcnow(),
      )

    except Exception as e:
      logger.error(f'Failed to get VENs active in last hour: {str(e)}')
      return ConsumptionServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )
