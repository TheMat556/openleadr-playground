from abc import ABC, abstractmethod
from typing import Dict, Any, List


class IDataManager(ABC):
  @abstractmethod
  async def update_consumption_data(self) -> None:
    pass

  @abstractmethod
  async def update_load_profile_data(self) -> None:
    pass

  @abstractmethod
  def get_data_buffer(self, container_name: str) -> Dict[str, List[Dict[str, Any]]]:
    pass

  @abstractmethod
  def _convert_timestamp(self, timestamp: int) -> int:
    pass
