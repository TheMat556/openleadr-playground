from abc import ABC, abstractmethod
from typing import List, Optional

from src.adr_node.database.domain.results.consumption_batch_result import (
  ConsumptionBatchResult,
)
from src.adr_node.database.domain.data.consumption_data import ConsumptionData
from src.adr_node.database.domain.query.consumption_query import ConsumptionQuery
from src.adr_node.database.domain.results.consumption_service_result import (
  ConsumptionServiceResult,
)


class IConsumptionService(ABC):
  """
  Interface for consumption service operations.

  Attributes
  ----------
  data : ConsumptionData
      The consumption data entity to be created.
  consumption_id : int
      The ID of the consumption record to be found.
  timestamp : int
      The timestamp for finding active consumption data.
  query : ConsumptionQuery
      The query criteria for finding consumption data.
  max_distance : Optional[int]
      The maximum distance for finding the nearest consumption record.
  target_timestamp : int
      The target timestamp for finding the closest consumption points.
  time_window_ms : int
      The time window in milliseconds for finding the closest consumption points.
  ven_id : str
      The VEN identifier for finding the closest consumption point.
  resource_id : str
      The resource identifier for finding the closest consumption point.
  """

  @abstractmethod
  def create_consumption_record(
    self, data: ConsumptionData
  ) -> ConsumptionServiceResult:
    """Create a single consumption record."""
    pass

  @abstractmethod
  def create_consumption_batch(
    self, data: List[ConsumptionData]
  ) -> ConsumptionBatchResult:
    """Create multiple consumption records in batch."""
    pass

  @abstractmethod
  def find_consumption_by_id(self, consumption_id: int) -> ConsumptionServiceResult:
    """Find a consumption record by its ID."""
    pass

  @abstractmethod
  def find_active_consumption(self, timestamp: int) -> ConsumptionServiceResult:
    """Find active consumption data at a specific timestamp."""
    pass

  @abstractmethod
  def find_consumption_by_criteria(
    self, query: ConsumptionQuery
  ) -> ConsumptionServiceResult:
    """Find consumption data matching specific criteria."""
    pass

  @abstractmethod
  def find_nearest_consumption(
    self, timestamp: int, max_distance: Optional[int] = None
  ) -> ConsumptionServiceResult:
    """Find the nearest consumption record to a timestamp."""
    pass

  @abstractmethod
  def get_ven_statistics(self) -> ConsumptionServiceResult:
    """Get statistics about VEN consumption."""
    pass

  @abstractmethod
  def get_closest_consumption_points(
    self, target_timestamp: int, time_window_ms: int
  ) -> ConsumptionServiceResult:
    """Find the closest consumption points within a time window."""
    pass

  @abstractmethod
  def get_closest_consumption_point(
    self, timestamp: int, ven_id: str, resource_id: str
  ) -> ConsumptionServiceResult:
    """Find the closest consumption point for a specific VEN and resource."""
    pass

  @abstractmethod
  def get_current_consumption(self) -> ConsumptionServiceResult:
    """Get the current consumption data."""
    pass

  @abstractmethod
  def get_vens_active_last_hour(self) -> ConsumptionServiceResult:
    """Get the VENs that were active in the last hour."""
    pass
