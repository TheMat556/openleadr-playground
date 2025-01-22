from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class IConsumptionService(ABC):
  @abstractmethod
  def insert_consumption(self, data: Dict[str, Any]) -> None:
    """Insert a single consumption record."""
    pass

  @abstractmethod
  def process_consumption_data(self, data: List[Dict[str, Any]]) -> None:
    """Process and save batch consumption data."""
    pass

  @abstractmethod
  def get_current_consumption(self, timestamp: int) -> Dict[str, Any]:
    """Get current consumption data."""
    pass

  @abstractmethod
  def get_closest_consumption(
    self, timestamp: int, ven_id: str, resource_id: str
  ) -> Optional[Dict[str, Any]]:
    """Get closest consumption data point."""
    pass

  @abstractmethod
  def get_ven_count(self) -> int:
    """Get count of unique VENs."""
    pass
