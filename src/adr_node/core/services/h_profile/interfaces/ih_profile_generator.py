from abc import ABC, abstractmethod
import numpy as np


class IHProfileGenerator(ABC):
  """Interface for H-profile generation."""

  @abstractmethod
  def generate_profile(self, t: float) -> float:
    """Generate a single H-profile value for time t."""
    pass

  @abstractmethod
  def generate_profile_batch(self, t_values: np.ndarray) -> np.ndarray:
    """Generate H-profile values for multiple time points."""
    pass
