from datetime import datetime
from typing import List, Optional
import numpy as np
from numpy.typing import NDArray

from src.adr_node.database.domain.data.z_value_data import ZValueData
from src.adr_node.database.domain.query.z_value_query import ZValueQuery
from src.adr_node.database.domain.results.z_value_service_result import (
  ZValueServiceResult,
)
from src.adr_node.database.domain.results.z_value_batch_result import ZValueBatchResult
from src.adr_node.database.interfaces.repositories.iz_value_repository import (
  IZValueRepository,
)
from src.adr_node.database.interfaces.services.iz_value_service import IZValueService
import logging


class ZValueService(IZValueService):
  def __init__(self, repository: IZValueRepository):
    self.repository = repository

  def create_z_value_record(self, data: ZValueData) -> ZValueServiceResult:
    try:
      self._validate_z_value_data(data)
      result = self.repository.create(data)
      return ZValueServiceResult(success=True, data=result, timestamp=datetime.utcnow())
    except Exception as e:
      logging.error(f'Failed to create z-value record: {str(e)}')
      return ZValueServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )

  def create_z_value_batch(self, data: List[ZValueData]) -> ZValueBatchResult:
    if not data:
      return ZValueBatchResult(
        successful_records=0, failed_records=0, errors=['No data provided']
      )

    successful = []
    errors = []

    for record in data:
      try:
        self._validate_z_value_data(record)
        successful.append(record)
      except ValueError as e:
        errors.append(f'Validation error for record: {str(e)}')

    if successful:
      try:
        self.repository.create_batch(successful)
      except Exception as e:
        return ZValueBatchResult(
          successful_records=0,
          failed_records=len(data),
          errors=[f'Batch insertion failed: {str(e)}'],
        )

    return ZValueBatchResult(
      successful_records=len(successful),
      failed_records=len(data) - len(successful),
      errors=errors,
    )

  def find_z_values_by_criteria(self, query: ZValueQuery) -> ZValueServiceResult:
    try:
      if query.timestamp_start and query.timestamp_end:
        result = self.repository.find_by_timestamp_range(
          query.timestamp_start, query.timestamp_end
        )
      elif query.ven_id:
        result = self.repository.find_by_ven(query.ven_id, query.limit)
      else:
        return ZValueServiceResult(
          success=False,
          error='Invalid query criteria',
          timestamp=datetime.utcnow(),
        )

      return ZValueServiceResult(
        success=True,
        data={
          'z_values': result,
          'count': len(result),
          'query_params': {
            'timestamp_start': query.timestamp_start,
            'timestamp_end': query.timestamp_end,
            'ven_id': query.ven_id,
            'limit': query.limit,
          },
        },
        timestamp=datetime.utcnow(),
      )
    except Exception as e:
      logging.error(f'Failed to find z-values by criteria: {str(e)}')
      return ZValueServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )

  def get_latest_z_values(
    self, time_window_ms: Optional[int] = None
  ) -> ZValueServiceResult:
    try:
      result = self.repository.get_latest_z_values(time_window_ms)
      return ZValueServiceResult(
        success=True,
        data={
          'z_values': result,
          'count': len(result),
          'time_window_ms': time_window_ms,
          'query_timestamp': datetime.utcnow().timestamp() * 1000,
        },
        timestamp=datetime.utcnow(),
      )
    except Exception as e:
      logging.error(f'Failed to get latest z-values: {str(e)}')
      return ZValueServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )

  def save_z_values(
    self, ven_ids: NDArray[np.str_], z_values: NDArray[np.float64], timestamp: int
  ) -> ZValueServiceResult:
    try:
      # Validate input arrays
      if len(ven_ids) != len(z_values):
        raise ValueError('Length mismatch between ven_ids and z_values arrays')

      if len(ven_ids) == 0:
        raise ValueError('Empty arrays provided')

      # Validate timestamp
      if timestamp <= 0:
        raise ValueError('Invalid timestamp provided')

      result = self.repository.save_z_values(ven_ids, z_values, timestamp)

      return ZValueServiceResult(
        success=result['success'] > 0,
        data={
          'successful_records': result['success'],
          'failed_records': result['failed'],
          'timestamp': timestamp,
          'ven_count': len(ven_ids),
          'saved_at': datetime.utcnow(),
        },
        error=str(result['errors'][0]) if result['errors'] else None,
        timestamp=datetime.utcnow(),
      )
    except Exception as e:
      logging.error(f'Failed to save z-values: {str(e)}')
      return ZValueServiceResult(
        success=False, error=str(e), timestamp=datetime.utcnow()
      )

  def _validate_z_value_data(self, data: ZValueData) -> None:
    """Validate z-value data before processing."""
    if not data.ven_id:
      raise ValueError('VEN ID is required')

    if data.z_value < 0:
      raise ValueError('Z-value cannot be negative')

    if data.timestamp <= 0:
      raise ValueError('Invalid timestamp')

    if not isinstance(data.created_at, datetime):
      raise ValueError('created_at must be a datetime object')

    if data.updated_at and not isinstance(data.updated_at, datetime):
      raise ValueError('updated_at must be a datetime object')

    # Validate timestamp is not in the future
    current_time = datetime.utcnow().timestamp() * 1000
    if data.timestamp > current_time + 60000:  # Allow 1 minute future tolerance
      raise ValueError('Timestamp cannot be in the future')
