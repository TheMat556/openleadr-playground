from typing import Dict, Any, List

from src.network_dashobard.config.container_config import ContainerConfig
from src.network_dashobard.interfaces.idata_manager import IDataManager
from src.network_dashobard.services.services import IHttpClient, ITimeService


class DataManager(IDataManager):
  def __init__(
    self,
    http_client: IHttpClient,
    time_service: ITimeService,
    configs: List[ContainerConfig],
    max_buffer_size: int,
  ):
    self.http_client = http_client
    self.time_service = time_service
    self.configs = configs
    self.max_buffer_size = max_buffer_size
    self.data_buffers: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}

  async def update_consumption_data(self) -> None:
    """Fetches and updates consumption data for all containers"""
    for config in self.configs:
      data = await self.http_client.fetch_data(config, 'consumption')
      if data:
        await self._process_consumption_data(config, data)

  async def update_load_profile_data(self) -> None:
    """Fetches and updates load profile data for all containers"""
    for config in self.configs:
      data = await self.http_client.fetch_data(config, 'load-profile')
      if data:
        await self._process_load_profile_data(config, data)

  def get_data_buffer(self, container_name: str) -> Dict[str, List[Dict[str, Any]]]:
    """Gets the data buffer for a specific container"""
    return self.data_buffers.get(
      container_name, {'consumption': [], 'load_profile': []}
    )

  def _convert_timestamp(self, timestamp: int) -> int:
    """Converts timestamp using the time service"""
    return self.time_service.convert_timestamp(timestamp)
