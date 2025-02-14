from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import numpy as np
from numpy.typing import NDArray

from src.adr_node.database.domain.data.z_value_data import ZValueData


class IZValueRepository(ABC):
  @abstractmethod
  def create(self, entity: ZValueData) -> ZValueData:
    """Create a single z-value record."""
    pass

  @abstractmethod
  def create_batch(self, entities: List[ZValueData]) -> List[ZValueData]:
    """Create multiple z-value records."""
    pass

  @abstractmethod
  def find_by_timestamp_range(
    self, start_timestamp: int, end_timestamp: int
  ) -> List[ZValueData]:
    """Find z-values within a timestamp range."""
    pass

  @abstractmethod
  def find_by_ven(self, ven_id: str, limit: int = 100) -> List[ZValueData]:
    """Find z-values for a specific VEN."""
    pass

  @abstractmethod
  def get_latest_z_values(
    self, time_window_ms: Optional[int] = None
  ) -> List[ZValueData]:
    """Get the most recent z-values."""
    pass

  @abstractmethod
  def save_z_values(
    self, ven_ids: NDArray[np.str_], z_values: NDArray[np.float64], timestamp: int
  ) -> Dict[str, Any]:
    """Save z-values for multiple VENs."""
    pass
