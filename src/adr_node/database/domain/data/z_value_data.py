from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ZValueData:
  """
  Immutable data class representing a z-value entry.
  """

  timestamp: int
  ven_id: str
  z_value: float
  created_at: Optional[int] = None
  updated_at: Optional[int] = None
