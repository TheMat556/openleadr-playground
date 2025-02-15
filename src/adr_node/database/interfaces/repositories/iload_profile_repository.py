from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class ILoadProfileRepository(ABC):
  """
  Interface for load profile repository operations.

  Attributes
  ----------
  data : List[Dict[str, Any]]
      The load profile data to be saved.
  limit : Optional[int]
      The maximum number of load profiles to retrieve.
  offset : Optional[int]
      The offset for the load profiles to retrieve.
  order_by : str
      The order by which to sort the load profiles.
  target_timestamp : int
      The target timestamp to find the closest point.
  """

  @abstractmethod
  def save_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Save load profile data."""
    pass

  @abstractmethod
  def get_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'dstart ASC',
  ) -> Dict[str, np.ndarray]:
    """Retrieve load profile data."""
    pass

  @abstractmethod
  def get_closest_point(self, target_timestamp: int) -> Optional[Dict[str, Any]]:
    """Get the closest load profile point to the target timestamp."""
    pass
