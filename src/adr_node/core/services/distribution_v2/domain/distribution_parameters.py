from dataclasses import dataclass


@dataclass
class DistributionParameters:
  time_window_ms: int = 900000  # 15 minutes
  max_g_value: float = 0.8
  correction_factor_a: float = 5.0
  correction_factor_b: float = 1.5
  correction_factor_c: float = 1.085
