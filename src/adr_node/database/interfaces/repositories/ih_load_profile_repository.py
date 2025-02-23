from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class IHLoadProfileRepository(ABC):
  """Interface for H-load profile repository operations."""

  @abstractmethod
  def save_h_load_profile(
    self, data: List[Dict[str, Any]], ven_id: Optional[str] = None
  ) -> Dict[str, Any]:
    """Save H-load profile data."""
    pass

  @abstractmethod
  def get_h_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'timestamp ASC',
    ven_id: Optional[str] = None,
  ) -> Dict[str, np.ndarray]:
    """Retrieve H-load profile data."""
    pass

  @abstractmethod
  def get_current_h_load_profile(
    self, ven_id: Optional[str] = None
  ) -> Optional[Dict[str, Any]]:
    """Get the most recent H-load profile value."""
    pass
