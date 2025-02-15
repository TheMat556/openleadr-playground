from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class IDatabaseService(ABC):
  """
  Interface for database service operations.

  Attributes
  ----------
  query : str
      The SQL query to be executed.
  params : Optional[List[Any]]
      The parameters for the SQL query.
  batch_values : List[List[Any]]
      The batch of values to be executed in the query.
  """

  @abstractmethod
  def execute_query(
    self, query: str, params: Optional[List[Any]] = None
  ) -> List[Dict[str, Any]]:
    """Execute a query and return the results."""
    pass

  @abstractmethod
  def execute_batch(self, query: str, batch_values: List[List[Any]]) -> None:
    """Execute a batch of queries."""
    pass
