from datetime import datetime, timezone
from typing import List, Optional, Union
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
    self,
    ven_ids: NDArray[np.str_],
    z_values: NDArray[np.float64],
    timestamps: Union[int, NDArray[np.int64]],
  ) -> ZValueServiceResult:
    """
    Save z-values for VENs.
    Last updated: 2025-02-21 17:01:38 UTC by TheMat556

    Parameters
    ----------
    ven_ids : NDArray[np.str_]
        Array of VEN IDs
    z_values : NDArray[np.float64]
        Array of z-values
    timestamps : Union[int, NDArray[np.int64]]
        Single timestamp or array of timestamps corresponding to each z-value

    Returns
    -------
    ZValueServiceResult
        Result of the save operation
    """
    try:
      # Validate input arrays
      if len(ven_ids) != len(z_values):
        raise ValueError('Length mismatch between ven_ids and z_values arrays')

      if len(ven_ids) == 0:
        raise ValueError('Empty arrays provided')

      # Convert single timestamp to array if needed
      if isinstance(timestamps, (int, np.integer)):
        timestamps = np.full(len(ven_ids), timestamps)
      elif len(timestamps) != len(ven_ids):
        raise ValueError('Length mismatch between timestamps and ven_ids arrays')

      # Validate timestamps
      if np.any(timestamps <= 0):
        raise ValueError('Invalid timestamp(s) provided')

      # Create batch data with unique combinations
      current_time = datetime.now(timezone.utc)
      batch_data = []
      seen_combinations = set()

      for ven_id, z_value, ts in zip(ven_ids, z_values, timestamps):
        # Create unique key for this combination
        key = (int(ts), str(ven_id))

        # Skip if we've already seen this combination
        if key in seen_combinations:
          continue

        seen_combinations.add(key)

        batch_data.append(
          ZValueData(
            ven_id=str(ven_id),
            z_value=float(z_value),
            timestamp=int(ts),
            created_at=current_time,
            updated_at=None,
          )
        )

      result = self.create_z_value_batch(batch_data)

      return ZValueServiceResult(
        success=result.successful_records > 0,
        data={
          'successful_records': result.successful_records,
          'failed_records': result.failed_records,
          'timestamps': timestamps,
          'ven_count': len(set(ven_ids)),
          'saved_at': current_time,
        },
        error=str(result.errors[0]) if result.errors else None,
        timestamp=current_time,
      )
    except Exception as e:
      logging.error(f'Failed to save z-values: {str(e)}')
      return ZValueServiceResult(
        success=False, error=str(e), timestamp=datetime.now(timezone.utc)
      )

  def save_z_values_for_intervals(self, data: dict, timestamp: int) -> dict:
    """
    Save z-values for intervals from a daily distribution.

    The data parameter is expected to be a dictionary with a key "ven_final_z_values"
    mapping each VEN ID to a list of 96 z-values.

    For each ven, a record will be created per interval. The timestamp for each record
    is adjusted by adding the interval index to the provided timestamp.

    Parameters
    ----------
    data : dict
        Dictionary containing the key "ven_final_z_values" with structure:
          { ven_id: [z0, z1, ..., z95], ... }
    timestamp : int
        Base timestamp (in ms) for the records.

    Returns
    -------
    dict
        Dictionary with the keys:
          - "success": bool indicating if at least one record was saved,
          - "batch_result": the result from the batch insertion,
          - "error": optional error message.
    """
    try:
      ven_final_z_values = data.get('ven_final_z_values')
      if not ven_final_z_values:
        return {
          'success': False,
          'error': 'No ven_final_z_values provided in data',
        }

      current_time = datetime.now(timezone.utc)
      batch_data = []
      for ven_id, z_list in ven_final_z_values.items():
        # Ensure z_list is a list
        if not isinstance(z_list, list):
          continue
        for i, z_val in enumerate(z_list):
          # Adjust timestamp for each interval (e.g., add interval index)
          record_ts = timestamp + i
          batch_data.append(
            ZValueData(
              ven_id=str(ven_id),
              z_value=float(z_val),
              timestamp=record_ts,
              created_at=current_time,
              updated_at=None,
            )
          )

      if not batch_data:
        return {'success': False, 'error': 'No valid z-value records to save.'}

      result = self.create_z_value_batch(batch_data)

      return {
        'success': result.successful_records > 0,
        'batch_result': result,
      }
    except Exception as e:
      logging.error(f'Failed to save z-values for intervals: {str(e)}')
      return {'success': False, 'error': str(e)}

  def get_last_inserted_z_values(
    self,
    ven_ids: NDArray[np.str_],
  ) -> List[ZValueData]:
    """
    Get the most recently inserted z-values for specified VEN IDs.
    Last updated: 2025-02-21 17:36:41 UTC by TheMat556

    Parameters
    ----------
    ven_ids : NDArray[np.str_]
        Array of VEN IDs to get z-values for

    Returns
    -------
    List[ZValueData]
    """
    try:
      if len(ven_ids) == 0:
        return []

      results = self.repository.get_last_inserted_z_values(ven_ids=ven_ids)

      return results

    except Exception as e:
      logging.error(
        f'Failed to get last inserted z-values at {datetime.now(timezone.utc).isoformat()}: {str(e)}'
      )
      return []

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
