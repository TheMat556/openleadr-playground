from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np


class IDatabaseManager(ABC):
  @abstractmethod
  def connect(self) -> None:
    pass

  @abstractmethod
  def disconnect(self) -> None:
    pass

  @abstractmethod
  def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
    pass

  @abstractmethod
  def insert_values_batch(
    self,
    table_name: str,
    columns: List[str],
    batch_values: List[List[Any]],
    conflict_cols: List[str],
  ) -> None:
    pass

  @abstractmethod
  def execute_query(self, query: str, params: List[Any] = []) -> List[Dict[str, Any]]:
    pass


class IEnergyDatabaseController(ABC):
  @abstractmethod
  def convert_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, np.ndarray]:
    pass

  @abstractmethod
  def insert_load_profile(
    self, data: List[Dict[str, Any]]
  ) -> Dict[str, int | List[Any]]:
    pass

  @abstractmethod
  def get_load_profile(
    self, limit: int = None, offset: int = None, order_by: str = 'dstart ASC'
  ) -> Dict[str, np.ndarray]:
    pass

  @abstractmethod
  def insert_consumption(self, data: Dict[str, Any]) -> None:
    pass

  @abstractmethod
  def get_consumption(self) -> Dict[str, np.ndarray]:
    pass


class IRestAPIController:
  pass
