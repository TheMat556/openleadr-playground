from abc import abstractmethod
from typing import List, Optional

from src.adr_node.database.domain.data.consumption_data import ConsumptionData
from src.adr_node.database.domain.query.consumption_query import ConsumptionQuery
from src.adr_node.database.interfaces.repositories.ibase_repository import (
  IBaseRepository,
)


class IConsumptionRepository(IBaseRepository[ConsumptionData, ConsumptionQuery]):
  """
  Interface for consumption repository operations.

  Attributes
  ----------
  T : TypeVar
      The type of the entity.
  Q : TypeVar
      The type of the query criteria.
  """

  @abstractmethod
  def find_by_timestamp_range(
    self, start_timestamp: int, end_timestamp: int
  ) -> List[ConsumptionData]:
    """Find consumption data within a timestamp range."""
    pass

  @abstractmethod
  def find_by_ven(self, ven_id: str, limit: int = 100) -> List[ConsumptionData]:
    """Find consumption data for a specific VEN."""
    pass

  @abstractmethod
  def find_by_resource(
    self, resource_id: str, limit: int = 100
  ) -> List[ConsumptionData]:
    """Find consumption data for a specific resource."""
    pass

  @abstractmethod
  def find_nearest_to_timestamp(
    self, timestamp: int, max_distance: Optional[int] = None
  ) -> Optional[ConsumptionData]:
    """Find the consumption data point nearest to the given timestamp."""
    pass

  @abstractmethod
  def count_unique_vens(self) -> int:
    """Count the number of unique VENs."""
    pass

  @abstractmethod
  def get_latest_readings(self, limit: int = 10) -> List[ConsumptionData]:
    """Get the most recent consumption readings."""
    pass

  @abstractmethod
  def find_closest_consumption_points(
    self, target_timestamp: int, time_window_ms: Optional[int] = None
  ) -> List[ConsumptionData]:
    """Find closest consumption points for all VENs."""
    pass

  @abstractmethod
  def find_closest_consumption_for_ven(
    self, target_timestamp: int, ven_id: str, time_window_ms: Optional[int] = None
  ) -> Optional[ConsumptionData]:
    """Find closest consumption point for a specific VEN."""
    pass
