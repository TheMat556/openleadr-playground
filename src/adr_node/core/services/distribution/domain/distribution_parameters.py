from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class DistributionParameters:
  """Immutable configuration parameters for load distribution calculations."""

  correction_factor_a: float = field(default=5.0)
  correction_factor_b: float = field(default=1.5)
  correction_factor_c: float = field(default=1.085)
  max_g_value: float = field(default=0.8)
  interval_duration_ms: int = field(default=900000)  # 15 minutes
  time_window_ms: Optional[int] = field(default=None)

  def __post_init__(self):
    object.__setattr__(self, 'correction_factor_a', self.correction_factor_a or 5.0)
    object.__setattr__(self, 'correction_factor_b', self.correction_factor_b or 1.5)
    object.__setattr__(self, 'correction_factor_c', self.correction_factor_c or 1.085)
    object.__setattr__(self, 'max_g_value', self.max_g_value or 0.8)
    object.__setattr__(
      self, 'interval_duration_ms', self.interval_duration_ms or 900000
    )
    object.__setattr__(self, 'time_window_ms', self.time_window_ms)
