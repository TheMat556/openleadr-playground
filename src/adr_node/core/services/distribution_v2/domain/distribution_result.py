from dataclasses import dataclass
from typing import Optional, Dict, List, Any
import numpy as np
from numpy.typing import NDArray


@dataclass
class DistributionResult:
  success: bool
  timestamp: int
  error: Optional[str] = None
  ven_ids: Optional[NDArray[np.str_]] = None
  z_values: Optional[NDArray[np.float64]] = None
  total_allowed: Optional[float] = None
  profiles: Optional[Dict[str, List[Dict[str, Any]]]] = None
  intervals: Optional[List[Dict[str, Any]]] = None
  stats: Optional[Dict[str, Any]] = None
