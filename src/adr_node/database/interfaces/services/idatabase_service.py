from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class IDatabaseService(ABC):
  @abstractmethod
  def execute_query(
    self, query: str, params: Optional[List[Any]] = None
  ) -> List[Dict[str, Any]]:
    pass

  @abstractmethod
  def execute_batch(self, query: str, batch_values: List[List[Any]]) -> None:
    pass
