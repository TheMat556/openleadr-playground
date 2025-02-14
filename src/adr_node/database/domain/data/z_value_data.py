from dataclasses import dataclass


@dataclass(frozen=True)
class ZValueData:
  """Immutable data class representing a z-value entry."""

  timestamp: int
  ven_id: str
  z_value: float
