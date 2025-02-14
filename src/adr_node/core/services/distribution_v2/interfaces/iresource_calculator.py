from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Union, List
import numpy as np
from numpy.typing import NDArray


class IResourceCalculator(ABC):
  @abstractmethod
  def set_z_value(self, value: Optional[Union[float, NDArray[np.float64]]]) -> None:
    pass

  @abstractmethod
  def calculate_load_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    total_allowed: float,
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    pass

  @abstractmethod
  def calculate_z_value(
    self,
    current_allowed_consumption: Dict[str, Any],
    active_vens_count: int,
    pending_vens_count: int,
  ) -> float:
    pass

  @abstractmethod
  def process_latest_z_values(
    self, latest_z_values: List[Dict[str, Any]], ven_ids: NDArray[np.str_]
  ) -> Optional[NDArray[np.float64]]:
    pass
