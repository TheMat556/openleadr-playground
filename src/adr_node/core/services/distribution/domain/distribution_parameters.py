from dataclasses import dataclass


@dataclass
class DistributionParameters:
  """
  Data class for distribution parameters in the OpenADR system.

  Attributes
  ----------
  time_window_ms : int
      The time window in milliseconds (default is 15 minutes).
  max_g_value : float
      The maximum G value (default is 0.8).
  correction_factor_a : float
      Correction factor A (default is 5.0).
  correction_factor_b : float
      Correction factor B (default is 1.5).
  correction_factor_c : float
      Correction factor C (default is 1.085).
  """

  time_window_ms: int = 900000  # 15 minutes
  max_g_value: float = 0.8
  correction_factor_a: float = 5.0
  correction_factor_b: float = 1.5
  correction_factor_c: float = 1.085
