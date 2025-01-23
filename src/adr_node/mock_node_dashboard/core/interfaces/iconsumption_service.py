from abc import ABC, abstractmethod
from typing import Optional

from src.adr_node.mock_node_dashboard.core.domains.consumption_data import (
  ConsumptionData,
)


class IConsumptionService(ABC):
  @abstractmethod
  def get_consumption_summary(self) -> Optional[ConsumptionData]:
    pass

  @abstractmethod
  def get_current_consumption(self) -> float:
    pass
