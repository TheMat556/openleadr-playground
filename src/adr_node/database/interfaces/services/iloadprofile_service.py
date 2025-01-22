from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class ILoadProfileService(ABC):
  @abstractmethod
  def process_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    pass

  @abstractmethod
  def get_load_profile_data(
    self, limit: Optional[int] = None, offset: Optional[int] = None
  ) -> Dict[str, np.ndarray]:
    pass

  @abstractmethod
  def get_closest_load_point(self, timestamp: int) -> Optional[Dict[str, Any]]:
    pass
