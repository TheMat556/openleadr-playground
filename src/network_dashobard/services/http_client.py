import os
import aiohttp
from typing import Dict, Any, Optional

import logging

from src.network_dashobard.config.container_config import ContainerConfig
from src.network_dashobard.services.services import IHttpClient
from src.node_dashboard.helper.constants import Environment


class HttpClient(IHttpClient):
  def __init__(self, timeout: int = 30):
    self.timeout = timeout
    self.session: Optional[aiohttp.ClientSession] = None

  async def __aenter__(self):
    self.session = aiohttp.ClientSession(
      timeout=aiohttp.ClientTimeout(total=self.timeout),
      connector=aiohttp.TCPConnector(
        keepalive_timeout=30, force_close=False, enable_cleanup_closed=True
      ),
    )
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    if self.session:
      await self.session.close()

  async def fetch_data(self, config: ContainerConfig, endpoint: str) -> Dict[str, Any]:
    """Fetches data from a specified endpoint for a container"""
    if not self.session:
      self.session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=self.timeout)
      )

    env = os.getenv('DOCKER_ENVIRONMENT', Environment.DOCKER)
    base_url = self._get_base_url(config, env == Environment.LOCAL)
    url = f'{base_url}/api/{endpoint}'

    try:
      async with self.session.get(
        url, headers={'Accept': 'application/json'}
      ) as response:
        if response.status == 200:
          return await response.json()
        else:
          logging.error(f'HTTP {response.status} from {url}: {await response.text()}')
          return {}
    except Exception as e:
      logging.error(f'Error fetching from {url}: {str(e)}')
      return {}

  def _get_base_url(self, config: ContainerConfig, is_local: bool) -> str:
    """Constructs the base URL based on environment"""
    if is_local:
      return f'http://localhost:{config.rest_api_port}'
    return f'http://{config.container_name}:{config.rest_api_port}'
