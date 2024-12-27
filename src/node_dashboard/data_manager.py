import os
import json
import asyncio
from typing import Dict, Any, Optional, List
import aiohttp
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

from jsonschema.exceptions import ValidationError
from jsonschema.validators import validate

from src.node_dashboard.helper.constants import Environment
from src.node_dashboard.helper.utils import fetch_data_async
from src.node_dashboard.helper.config import ContainerConfig

logger = logging.getLogger(__name__)


class DataManager:
  """
  Manages data fetching and buffering for container configurations.

  Attributes
  ----------
  configs : List[ContainerConfig]
      List of container configurations.
  data_buffers : Dict[str, Dict[str, List[Dict[str, Any]]]]
      Buffers to store fetched data.
  max_buffer_size : int
      Maximum size of the data buffers.
  """

  def __init__(self, configs: List[ContainerConfig], max_buffer_size: int):
    """
    Initializes the DataManager with configurations and buffer size.

    Parameters
    ----------
    configs : List[ContainerConfig]
        List of container configurations.
    max_buffer_size : int
        Maximum size of the data buffers.
    """
    self.configs = configs
    self.data_buffers: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    self.max_buffer_size = max_buffer_size
    self.lock = asyncio.Lock()

  async def update_consumption_data(self) -> None:
    """
    Fetches and updates consumption data for each container.

    Returns
    -------
    None
    """
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
      tasks = [self._fetch_consumption_data(session, config) for config in self.configs]

      try:
        results = await asyncio.gather(*tasks)
        for idx, config in enumerate(self.configs):
          consumption_data = results[idx]
          if consumption_data:
            await self._process_consumption_data(config, consumption_data)
      except (aiohttp.ClientError, json.JSONDecodeError) as e:
        logger.error(f'Error fetching consumption data: {e}')

      logger.info('Consumption data updated for all containers.')

  async def update_load_profile_data(self) -> None:
    """
    Fetches and updates load profile data for each container.

    Returns
    -------
    None
    """
    async with aiohttp.ClientSession() as session:
      tasks = [
        self._fetch_load_profile_data(session, config) for config in self.configs
      ]

      try:
        results = await asyncio.gather(*tasks)
        for idx, config in enumerate(self.configs):
          await self._process_load_profile_data(config, results[idx])
      except (aiohttp.ClientError, json.JSONDecodeError) as e:
        logger.error(f'Error fetching load profile data: {e}')

  @staticmethod
  @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=1, max=10))
  async def _fetch_consumption_data(
    session: aiohttp.ClientSession, config: ContainerConfig
  ) -> Optional[Dict[str, Any]]:
    """
    Fetches consumption data from the container's REST API with retry logic.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The aiohttp client session.
    config : ContainerConfig
        The container configuration.

    Returns
    -------
    Optional[Dict[str, Any]]
        The fetched consumption data.
    """
    env = os.getenv('DOCKER_ENVIRONMENT', Environment.DOCKER)
    is_local = env == Environment.LOCAL
    base_url = 'http://localhost' if is_local else config.vtn_self_host
    consumption_url = f'{base_url}:{config.rest_api_port}/data/consumption'
    return await fetch_data_async(session, consumption_url)

  @staticmethod
  async def _fetch_load_profile_data(
    session: aiohttp.ClientSession, config: ContainerConfig
  ) -> Optional[Dict[str, Any]]:
    """
    Fetches load profile data from the container's REST API.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The aiohttp client session.
    config : ContainerConfig
        The container configuration.

    Returns
    -------
    Optional[Dict[str, Any]]
        The fetched load profile data.
    """
    is_local = os.getenv('DOCKER_ENVIRONMENT', 'true') == 'false'
    base_url = 'http://localhost' if is_local else config.vtn_self_host
    load_profile_url = f'{base_url}:{config.rest_api_port}/data/load_profile'
    return await fetch_data_async(session, load_profile_url)

  async def _process_consumption_data(
    self, config: ContainerConfig, consumption_data: Dict[str, Any]
  ) -> None:
    """
    Processes and buffers the fetched consumption data.

    Parameters
    ----------
    config : ContainerConfig
        The container configuration.
    consumption_data : Dict[str, Any]
        The fetched consumption data.

    Returns
    -------
    None
    """
    schema = {
      'type': 'object',
      'properties': {
        'consumption': {
          'type': 'object',
          'properties': {'timestamp': {'type': 'string'}, 'value': {'type': 'number'}},
          'required': ['timestamp', 'value'],
        }
      },
      'required': ['consumption'],
    }

    async with self.lock:
      try:
        validate(instance=consumption_data, schema=schema)
        buffer = self.data_buffers.setdefault(
          config.container_name, {'consumption': [], 'load_profile': []}
        )
        buffer['consumption'].append(consumption_data['consumption'])
        if len(buffer['consumption']) > self.max_buffer_size:
          buffer['consumption'].pop(0)
        logger.info(f'Updated buffer for {config.container_name} (consumption)')
      except ValidationError as e:
        logger.error(
          f'Invalid consumption data format for {config.container_name}: {e.message}. Data: {consumption_data}'
        )
      except KeyError as e:
        logger.error(
          f'Invalid consumption data format for {config.container_name}: Missing key {e}. Data: {consumption_data}'
        )

  async def _process_load_profile_data(
    self, config: ContainerConfig, load_profile_data: Optional[Dict[str, Any]]
  ) -> None:
    """
    Processes and buffers the fetched load profile data.

    Parameters
    ----------
    config : ContainerConfig
        The container configuration.
    load_profile_data : Optional[Dict[str, Any]]
        The fetched load profile data.

    Returns
    -------
    None
    """
    if not load_profile_data:
      logger.warning(f'No load profile data received for {config.container_name}')
      return

    async with self.lock:
      try:
        buffer = self.data_buffers.setdefault(
          config.container_name, {'consumption': [], 'load_profile': []}
        )
        value_data = load_profile_data.get('value')
        if not isinstance(value_data, dict):
          raise ValueError(f'Expected dict for "value", got {type(value_data)}')

        valid_entries = [
          {'timestamp': time, 'value': value}
          for time, value in value_data.items()
          if isinstance(value, (int, float))
        ]

        buffer['load_profile'].extend(valid_entries)

        if len(buffer['load_profile']) > self.max_buffer_size:
          buffer['load_profile'] = buffer['load_profile'][-self.max_buffer_size :]
        logger.info(f'Updated buffer for {config.container_name} (load_profile)')
      except Exception as e:
        logger.error(
          f'Error processing load profile data for {config.container_name}: {e}'
        )
