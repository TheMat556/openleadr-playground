from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class ILoadProfileService(ABC):
  """
  Interface for load profile service operations.
  """

  @abstractmethod
  def save_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Save load profile data."""
    pass

  @abstractmethod
  def process_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process load profile data."""
    pass

  @abstractmethod
  def get_load_profile_data(
    self, limit: Optional[int] = None, offset: Optional[int] = None
  ) -> Dict[str, np.ndarray]:
    """Retrieve load profile data."""
    pass

  @abstractmethod
  def get_closest_load_point(self, timestamp: int) -> Optional[Dict[str, Any]]:
    """Find the closest load point to a timestamp."""
    pass
