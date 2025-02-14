from abc import ABC, abstractmethod
import numpy as np
from numpy.typing import NDArray

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.services.distribution.domain.distribution_result import (
  DistributionResult,
)


class IDistributionService(IRunnable, ABC):
  """Interface for distribution service operations."""

  @abstractmethod
  def update_load_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    timestamp: int,
  ) -> DistributionResult:
    """
    Calculate and update load distribution for given VENs.

    Args:
        ven_ids: Array of VEN identifiers
        consumption_values: Array of consumption values
        timestamp: Current timestamp in milliseconds

    Returns:
        DistributionResult containing calculation results or error
    """
    pass

  @abstractmethod
  def run(self) -> None:
    """
    Start the distribution service operations.
    Implementation should handle periodic updates and service lifecycle.
    """
    pass
