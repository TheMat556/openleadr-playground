from dataclasses import dataclass
from typing import Optional, Dict, List, Any
import numpy as np
from numpy.typing import NDArray


@dataclass
class DistributionResult:
  """
  Data class for distribution results in the OpenADR system.

  Attributes
  ----------
  success : bool
      Indicates if the distribution was successful.
  timestamp : int
      The timestamp of the distribution result.
  error : Optional[str]
      Error message if the distribution failed.
  ven_ids : Optional[NDArray[np.str_]]
      Array of VEN IDs.
  z_values : Optional[NDArray[np.float64]]
      Array of Z values.
  total_allowed : Optional[float]
      Total allowed consumption.
  profiles : Optional[Dict[str, List[Dict[str, Any]]]]
      Profiles of the distribution result.
  intervals : Optional[List[Dict[str, Any]]]
      Intervals of the distribution result.
  stats : Optional[Dict[str, Any]]
      Statistics of the distribution result.
  """

  success: bool
  timestamp: int
  error: Optional[str] = None
  ven_ids: Optional[NDArray[np.str_]] = None
  z_values: Optional[NDArray[np.float64]] = None
  total_allowed: Optional[float] = None
  profiles: Optional[Dict[str, List[Dict[str, Any]]]] = None
  intervals: Optional[List[Dict[str, Any]]] = None
  stats: Optional[Dict[str, Any]] = None
