from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class IConsumptionService(ABC):
  @abstractmethod
  def process_consumption_data(self, data: List[Dict[str, Any]]) -> None:
    pass

  @abstractmethod
  def get_current_consumption(self, timestamp: int) -> Dict[str, Any]:
    pass

  def get_closest_consumption(
    self, timestamp: int, ven_id: str, resource_id: str
  ) -> Optional[Dict[str, Any]]:
    pass

  @abstractmethod
  def get_ven_count(self) -> int:
    pass
