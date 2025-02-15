import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential
from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate
from src.network_dashboard.helper.constants import Environment
from src.network_dashboard.helper.config import ContainerConfig
from src.network_dashboard.helper.logger import logger


class DataManager:
  def __init__(self, configs: List[ContainerConfig], max_buffer_size: int):
    self.configs = configs
    self.data_buffers: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    self.max_buffer_size = max_buffer_size
    self.lock = asyncio.Lock()
    self.timezone_offset = timezone(timedelta(hours=1))

  def _convert_timestamp(self, timestamp: int) -> int:
    try:
      utc_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
      cet_dt = utc_dt.astimezone(self.timezone_offset)
      return int(cet_dt.timestamp() * 1000)
    except Exception as e:
      logger.error(f'Error converting timestamp {timestamp}: {e}')
      return timestamp * 1000

  @staticmethod
  @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
  async def _fetch_data(
    session: aiohttp.ClientSession, config: ContainerConfig, data_type: str
  ) -> Optional[Dict[str, Any]]:
    env = os.getenv('DOCKER_ENVIRONMENT', Environment.DOCKER)
    is_local = env == Environment.LOCAL

    base_url = (
      f'http://localhost:{config.rest_api_port}'
      if is_local
      else f'http://{config.container_name}:{config.rest_api_port}'
    )
    url = f'{base_url}/api/{data_type}'
    logger.debug(f'Fetching data from URL: {url}')

    try:
      async with session.get(
        url,
        timeout=aiohttp.ClientTimeout(total=5),
        headers={'Accept': 'application/json'},
      ) as response:
        if response.status == 200:
          return await response.json()
        logger.error(f'HTTP {response.status} from {url}: {await response.text()}')
        return None
    except Exception as e:
      logger.error(f'Error fetching from {url}: {str(e)}')
      raise

  async def update_consumption_data(self) -> None:
    timeout_seconds = int(os.getenv('DATA_FETCH_TIMEOUT', 30))
    connector = aiohttp.TCPConnector(
      keepalive_timeout=30, force_close=False, enable_cleanup_closed=True
    )
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async with aiohttp.ClientSession(
      timeout=timeout, connector=connector, raise_for_status=True
    ) as session:
      tasks = [
        self._fetch_data(session, config, 'consumption') for config in self.configs
      ]

      try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, result in enumerate(results):
          if isinstance(result, Exception):
            logger.error(
              f'Error fetching consumption data for {self.configs[idx].container_name}: {result}'
            )
            continue
          if result and result.get('status') == 'success':
            await self._process_consumption_data(
              self.configs[idx], result.get('data', {})
            )
      except Exception as e:
        logger.error(f'Unexpected error in update_consumption_data: {e}')

  async def update_load_profile_data(self) -> None:
    timeout_seconds = int(os.getenv('DATA_FETCH_TIMEOUT', 30))
    connector = aiohttp.TCPConnector(
      keepalive_timeout=30, force_close=False, enable_cleanup_closed=True
    )
    timeout = aiohttp.ClientTimeout(total=timeout_seconds)

    async with aiohttp.ClientSession(
      timeout=timeout, connector=connector, raise_for_status=True
    ) as session:
      tasks = [
        self._fetch_data(session, config, 'load-profile') for config in self.configs
      ]

      try:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for idx, result in enumerate(results):
          if isinstance(result, Exception):
            logger.error(
              f'Error fetching load profile data for {self.configs[idx].container_name}: {result}'
            )
            continue
          if result and result.get('status') == 'success':
            await self._process_load_profile_data(
              self.configs[idx], result.get('data', {})
            )
      except Exception as e:
        logger.error(f'Unexpected error in update_load_profile_data: {e}')

  async def _process_consumption_data(
    self, config: ContainerConfig, consumption_data: Dict[str, Any]
  ) -> None:
    schema = {
      'type': 'object',
      'properties': {
        'average_consumption': {'type': 'number'},
        'measurement_unit': {'type': 'string'},
        'statistics': {
          'type': 'object',
          'properties': {
            'point_count': {'type': 'integer'},
            'time_window': {
              'type': 'object',
              'properties': {
                'end': {'type': 'integer'},
                'start': {'type': 'integer'},
                'window_ms': {'type': 'integer'},
              },
              'required': ['end', 'start', 'window_ms'],
            },
          },
          'required': ['point_count', 'time_window'],
        },
        'timestamp': {'type': 'integer'},
        'total_consumption': {'type': 'number'},
      },
      'required': [
        'average_consumption',
        'measurement_unit',
        'statistics',
        'timestamp',
        'total_consumption',
      ],
    }

    logger.debug(f'Processing consumption data: {consumption_data}')

    async with self.lock:
      try:
        validate(instance=consumption_data, schema=schema)

        transformed_data = {
          'timestamp': self._convert_timestamp(
            consumption_data['statistics']['time_window']['end']
          ),
          'value': consumption_data['average_consumption'],
        }

        buffer = self.data_buffers.setdefault(
          config.container_name, {'consumption': [], 'load_profile': []}
        )

        buffer['consumption'].append(transformed_data)

        if len(buffer['consumption']) > self.max_buffer_size:
          buffer['consumption'] = buffer['consumption'][-self.max_buffer_size :]

        logger.debug(
          f'Updated consumption buffer for {config.container_name}: {transformed_data}'
        )

      except ValidationError as e:
        logger.error(
          f'Invalid consumption data format for {config.container_name}: {e.message}'
        )
      except Exception as e:
        logger.error(
          f'Error processing consumption data for {config.container_name}: {e}'
        )

  async def _process_load_profile_data(
    self, config: ContainerConfig, load_profile_data: Dict[str, Any]
  ) -> None:
    schema = {
      'type': 'object',
      'properties': {
        'dstart': {'type': 'array', 'items': {'type': 'integer'}},
        'duration': {'type': 'array', 'items': {'type': 'integer'}},
        'signal_payload': {'type': 'array', 'items': {'type': 'number'}},
      },
      'required': ['dstart', 'duration', 'signal_payload'],
    }

    if not load_profile_data:
      logger.warning(f'No load profile data received for {config.container_name}')
      return

    async with self.lock:
      try:
        validate(instance=load_profile_data, schema=schema)

        buffer = self.data_buffers.setdefault(
          config.container_name, {'consumption': [], 'load_profile': []}
        )

        min_length = min(
          len(load_profile_data['dstart']),
          len(load_profile_data['duration']),
          len(load_profile_data['signal_payload']),
        )

        valid_entries = [
          {
            'timestamp': self._convert_timestamp(load_profile_data['dstart'][i]),
            'duration': load_profile_data['duration'][i],
            'signal_payload': load_profile_data['signal_payload'][i],
          }
          for i in range(min_length)
        ]

        valid_entries.sort(key=lambda x: x['timestamp'])
        buffer['load_profile'].extend(valid_entries)

        if len(buffer['load_profile']) > self.max_buffer_size:
          buffer['load_profile'] = buffer['load_profile'][-self.max_buffer_size :]

        logger.debug(
          f'Updated load profile buffer for {config.container_name}: {len(valid_entries)} entries'
        )

      except ValidationError as e:
        logger.error(
          f'Invalid load profile data format for {config.container_name}: {e.message}'
        )
      except Exception as e:
        logger.error(
          f'Error processing load profile data for {config.container_name}: {e}'
        )
