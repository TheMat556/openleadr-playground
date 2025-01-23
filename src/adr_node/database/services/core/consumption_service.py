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
      print('target_timestamp', target_timestamp)
      points = self.repository.find_closest_consumption_points(
        target_timestamp, time_window_ms
      )
      print('!!!!')

      if not points:
        return ConsumptionServiceResult(
          success=False,
          error='No consumption points found',
          timestamp=datetime.utcnow(),
        )

      total_value = sum(point.value for point in points)

      return ConsumptionServiceResult(
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
