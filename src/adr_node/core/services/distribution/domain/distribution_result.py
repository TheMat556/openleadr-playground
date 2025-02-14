from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class DistributionResult:
  """Immutable result of load distribution calculations."""

  success: bool
  timestamp: int
  ven_ids: Optional[NDArray[np.str_]] = None
  z_values: Optional[NDArray[np.float64]] = None
  total_allowed: Optional[float] = None
  intervals: Optional[List[Dict[str, Any]]] = None
  stats: Optional[Dict[str, float]] = None
  error: Optional[str] = None
