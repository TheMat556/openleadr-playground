from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class ILoadProfileRepository(ABC):
  @abstractmethod
  def save_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    pass

  @abstractmethod
  def get_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'dstart ASC',
  ) -> Dict[str, np.ndarray]:
    pass

  @abstractmethod
  def get_closest_point(self, target_timestamp: int) -> Optional[Dict[str, Any]]:
    pass
