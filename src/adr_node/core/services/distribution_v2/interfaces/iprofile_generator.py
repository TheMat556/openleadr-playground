# src/adr_node/core/services/distribution/interfaces/iprofile_generator.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np
from numpy.typing import NDArray


class IProfileGenerator(ABC):
  @abstractmethod
  def create_ven_profiles(
    self,
    ven_ids: NDArray[np.str_],
    z_values: NDArray[np.float64],
    intervals: List[Dict[str, Any]],
  ) -> Dict[str, List[Dict[str, Any]]]:
    pass
