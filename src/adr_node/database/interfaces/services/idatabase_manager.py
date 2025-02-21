from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np


class IDatabaseManager(ABC):
  """
  Interface for database management operations.

  Attributes
  ----------
  table_name : str
      The name of the table to be created or modified.
  columns : Dict[str, str]
      The columns and their data types for the table.
  batch_values : List[List[Any]]
      The batch of values to be inserted into the table.
  conflict_cols : List[str]
      The columns to check for conflicts during batch insertion.
  query : str
      The SQL query to be executed.
  params : List[Any]
      The parameters for the SQL query.
  """

  @abstractmethod
  def connect(self) -> None:
    """Connect to the database."""
    pass

  @abstractmethod
  def disconnect(self) -> None:
    """Disconnect from the database."""
    pass

  @abstractmethod
  def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
    """Create a table in the database."""
    pass

  @abstractmethod
  def insert_values_batch(
    self,
    table_name: str,
    columns: List[str],
    batch_values: List[List[Any]],
    conflict_cols: List[str],
  ) -> None:
    """Insert a batch of values into a table."""
    pass

  @abstractmethod
  def execute_query(self, query: str, params: List[Any] = []) -> List[Dict[str, Any]]:
    """Execute a query and return the results."""
    pass


class IEnergyDatabaseController(ABC):
  """
  Interface for energy database controller operations.

  Attributes
  ----------
  data : List[Dict[str, Any]]
      The load profile data to be converted or inserted.
  limit : int
      The maximum number of load profiles to retrieve.
  offset : int
      The offset for the load profiles to retrieve.
  order_by : str
      The order by which to sort the load profiles.
  """

  @abstractmethod
  def convert_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    """Convert load profile data to a specific format."""
    pass

  @abstractmethod
  def insert_load_profile(
    self, data: List[Dict[str, Any]]
  ) -> Dict[str, int | List[Any]]:
    """Insert load profile data into the database."""
    pass

  @abstractmethod
  def get_load_profile(
    self, limit: int = None, offset: int = None, order_by: str = 'dstart ASC'
  ) -> Dict[str, np.ndarray]:
    """Retrieve load profile data from the database."""
    pass

  @abstractmethod
  def insert_consumption(self, data: Dict[str, Any]) -> None:
    """Insert consumption data into the database."""
    pass

  @abstractmethod
  def get_consumption(self) -> Dict[str, np.ndarray]:
    """Retrieve consumption data from the database."""
    pass


class IRestAPIController:
  """
  Interface for REST API controller operations.
  """

  pass
