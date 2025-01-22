from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np


class IConsumptionRepository(ABC):
  @abstractmethod
  def insert_consumption(self, data: Dict[str, Any]) -> None:
    """Insert a single consumption record."""
    pass

  @abstractmethod
  def save_consumption_batch(self, data: List[Dict[str, Any]]) -> None:
    """Save batch consumption data."""
    pass

  @abstractmethod
  def get_consumption(self) -> Dict[str, np.ndarray]:
    """Get all consumption data."""
    pass

  @abstractmethod
  def get_closest_consumption_points(
    self, target_timestamp: int
  ) -> List[Dict[str, Any]]:
    """Get closest consumption points."""
    pass

  @abstractmethod
  def get_unique_vens(self) -> int:
    """Get count of unique VENs."""
    pass
