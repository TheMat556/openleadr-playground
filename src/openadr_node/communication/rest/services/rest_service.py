# src/openadr_node/protocols/rest/services/rest_service.py
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, List
from injector import inject

from src.openadr_node import logger
from src.openadr_node.communication.rest.exceptions.exceptions import (
  DataNotFoundException,
  ServiceNotInitializedException,
  DataProcessingException,
  RestServiceException,
)
from src.openadr_node.communication.rest.interfaces.irest_service import IRestService
from src.openadr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.openadr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)


class RestService(IRestService):
  @inject
  def __init__(
    self,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
  ):
    self._load_profile_service = load_profile_service
    self._consumption_service = consumption_service

  def _process_consumption_points(
    self, points: List[Dict[str, Any]]
  ) -> Tuple[float, str]:
    if not points:
      raise DataNotFoundException('Consumption points')
    overall_value = sum(point['value'] for point in points)
    ven_id = points[0]['ven_id']
    return overall_value, ven_id

  def get_load_profile(self) -> Tuple[Dict[str, Any], int]:
    try:
      if not self._load_profile_service:
        raise ServiceNotInitializedException('LoadProfileService')

      df = self._load_profile_service.get_load_profile_data()
      if not df or not any(arr.size for arr in df.values()):
        raise DataNotFoundException('Load profile data')

      formatted_data = {
        str(int(start)): {'duration': int(dur), 'signal_payload': float(payload)}
        for start, dur, payload in zip(
          df['dstart'], df['duration'], df['signal_payload']
        )
      }

      return formatted_data, 200

    except RestServiceException as e:
      logger.error(f'Load profile error: {str(e)}')
      raise
    except Exception as e:
      logger.error(f'Unexpected error in get_load_profile: {str(e)}')
      raise DataProcessingException('load profile', str(e))

  def get_current_consumption(self) -> Tuple[Dict[str, Any], int]:
    try:
      if not self._consumption_service:
        raise ServiceNotInitializedException('ConsumptionService')

      current_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
      consumption_points = self._consumption_service.get_closest_consumption_points(
        current_timestamp
      )

      if not consumption_points:
        raise DataNotFoundException('Consumption data')

      overall_value, ven_id = self._process_consumption_points(consumption_points)

      return {
        'ven_id': ven_id,
        'overall_value': overall_value,
        'unit': 'kWh',
        'timestamp': current_timestamp,
      }, 200

    except RestServiceException as e:
      logger.error(f'Consumption error: {str(e)}')
      raise
    except Exception as e:
      logger.error(f'Unexpected error in get_current_consumption: {str(e)}')
      raise DataProcessingException('consumption data', str(e))
