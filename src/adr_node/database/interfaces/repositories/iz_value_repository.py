from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import numpy as np
from numpy.typing import NDArray

from src.adr_node.database.domain.data.z_value_data import ZValueData


class IZValueRepository(ABC):
  """
  Interface for z-value repository operations.

  Attributes
  ----------
  entity : ZValueData
      The z-value data entity to be created.
  entities : List[ZValueData]
      The list of z-value data entities to be created in batch.
  start_timestamp : int
      The start timestamp for finding z-values.
  end_timestamp : int
      The end timestamp for finding z-values.
  ven_id : str
      The VEN identifier for finding z-values.
  limit : int
      The maximum number of z-values to retrieve.
  time_window_ms : Optional[int]
      The time window in milliseconds for retrieving the latest z-values.
  ven_ids : NDArray[np.str_]
      The array of VEN identifiers for saving z-values.
  z_values : NDArray[np.float64]
      The array of z-values to be saved.
  timestamp : int
      The timestamp for saving z-values.
  """

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

  @abstractmethod
  def get_last_inserted_z_values(
    self,
    ven_ids: NDArray[np.str_],
  ) -> List[ZValueData]:
    """
    Get the last inserted z-values for specified VEN IDs that are before the reference timestamp.
    Last updated: 2025-02-21 17:27:55 UTC by TheMat556

    Parameters
    ----------
    ven_ids : NDArray[np.str_]
        Array of VEN IDs to get z-values for
    Returns
    -------
    List[ZValueData]
        List of last inserted z-values for each VEN
    """
    pass
