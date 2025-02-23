from abc import ABC, abstractmethod
from typing import List, Optional, Union

import numpy as np
from numpy.typing import NDArray

from src.adr_node.database.domain.data.z_value_data import ZValueData
from src.adr_node.database.domain.results.z_value_service_result import (
  ZValueServiceResult,
)


class IZValueService(ABC):
  """
  Interface for ZValueService which manages z-value records.
  """

  @abstractmethod
  def create_z_value_record(self, data: ZValueData) -> ZValueServiceResult:
    """
    Create a single z-value record.
    """
    pass

  @abstractmethod
  def create_z_value_batch(self, data: List[ZValueData]) -> object:
    """
    Create a batch of z-value records.
    """
    pass

  @abstractmethod
  def find_z_values_by_criteria(self, query) -> ZValueServiceResult:
    """
    Find z-value records based on query criteria.
    """
    pass

  @abstractmethod
  def get_latest_z_values(
    self, time_window_ms: Optional[int] = None
  ) -> ZValueServiceResult:
    """
    Retrieve the latest z-value records within an optional time window.
    If time_window_ms is provided, return all records with timestamp greater than or equal to (current_time - time_window_ms).
    Otherwise, return all records.
    """
    pass

  @abstractmethod
  def save_z_values(
    self,
    ven_ids: NDArray[np.str_],
    z_values: NDArray[np.float64],
    timestamps: Union[int, NDArray[np.int64]],
  ) -> ZValueServiceResult:
    """
    Save an array of z-values along with corresponding VEN IDs and timestamps.
    """
    pass

  @abstractmethod
  def save_z_values_for_intervals(self, data: dict, timestamp: int) -> dict:
    """
    Save daily distribution z-values for each VEN. The data should be a dict with key "ven_final_z_values"
    mapping each VEN ID to a list of 96 z-values.
    """
    pass

  @abstractmethod
  def get_last_inserted_z_values(self, ven_ids: NDArray[np.str_]) -> List[ZValueData]:
    """
    Retrieve the most recently inserted z-values for the given VEN IDs.
    """
    pass
