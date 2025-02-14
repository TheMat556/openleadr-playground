from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from numpy.typing import NDArray

from src.adr_node.database.domain.data.z_value_data import ZValueData
from src.adr_node.database.domain.query.z_value_query import ZValueQuery
from src.adr_node.database.domain.results.z_value_service_result import (
  ZValueServiceResult,
)
from src.adr_node.database.domain.results.z_value_batch_result import ZValueBatchResult


class IZValueService(ABC):
  @abstractmethod
  def create_z_value_record(self, data: ZValueData) -> ZValueServiceResult:
    """Create a single z-value record."""
    pass

  @abstractmethod
  def create_z_value_batch(self, data: List[ZValueData]) -> ZValueBatchResult:
    """Create multiple z-value records in batch."""
    pass

  @abstractmethod
  def find_z_values_by_criteria(self, query: ZValueQuery) -> ZValueServiceResult:
    """Find z-values matching specific criteria."""
    pass

  @abstractmethod
  def get_latest_z_values(
    self, time_window_ms: Optional[int] = None
  ) -> ZValueServiceResult:
    """Get the most recent z-values."""
    pass

  @abstractmethod
  def save_z_values(
    self, ven_ids: NDArray[np.str_], z_values: NDArray[np.float64], timestamp: int
  ) -> ZValueServiceResult:
    """Save z-values for multiple VENs."""
    pass
