# src/adr_node/core/services/distribution/interfaces/iprofile_generator.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np
from numpy.typing import NDArray


class IProfileGenerator(ABC):
  """
  Interface for Profile Generator in the OpenADR system.

  This interface defines the method to create VEN profiles based on Z values and intervals.

  Methods
  -------
  create_ven_profiles(ven_ids: NDArray[np.str_], z_values: NDArray[np.float64], intervals: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]
      Create profiles for the VENs.
  """

  @abstractmethod
  def create_ven_profiles(
    self,
    ven_ids: NDArray[np.str_],
    z_values: NDArray[np.float64],
    intervals: List[Dict[str, Any]],
  ) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create profiles for the VENs.

    Parameters
    ----------
    ven_ids : NDArray[np.str_]
        Array of VEN IDs.
    z_values : NDArray[np.float64]
        Array of Z values.
    intervals : List[Dict[str, Any]]
        List of intervals.

    Returns
    -------
    Dict[str, List[Dict[str, Any]]]
        Dictionary of VEN IDs and their corresponding profiles.
    """
    pass
