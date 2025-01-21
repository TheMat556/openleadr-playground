from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np


class IConsumptionRepository(ABC):
  @abstractmethod
  def save_consumption_batch(self, data: List[Dict[str, Any]]) -> None:
    pass

  @abstractmethod
  def get_consumption(self) -> Dict[str, np.ndarray]:
    pass

  @abstractmethod
  def get_closest_consumption_points(
    self, target_timestamp: int
  ) -> List[Dict[str, Any]]:
    pass

  @abstractmethod
  def get_unique_vens(self) -> int:
    pass
