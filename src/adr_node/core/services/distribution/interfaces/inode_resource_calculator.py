from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from numpy.typing import NDArray


class INodeResourceCalculator(ABC):
  """Interface for node resource calculation operations."""

  @abstractmethod
  def set_z_value(self, value: Optional[float]) -> None:
    """Set the z-value for load distribution calculations."""
    pass

  @abstractmethod
  def process_load_profile_data(
    self, data: List[Dict[str, Any]]
  ) -> List[Dict[str, Any]]:
    """Process and validate load profile data."""
    pass

  @abstractmethod
  def get_current_data(
    self, current_timestamp: int
  ) -> tuple[Optional[dict], Optional[list]]:
    """Get current allowed consumption and consumption points."""
    pass

  @abstractmethod
  def prepare_consumption_array(
    self, current_consumption: List[Dict[str, Any]]
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    """Prepare consumption data arrays."""
    pass

  @abstractmethod
  def calculate_z_value(
    self,
    current_allowed_consumption: Dict[str, Any],
    active_vens_count: int,
    pending_vens_count: int,
  ) -> float:
    """Calculate the initial Z value for load distribution."""
    pass

  @abstractmethod
  def calculate_load_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    total_allowed: float,
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    """Calculate load distribution."""
    pass

  @abstractmethod
  def generate_time_intervals(self) -> List[Dict[str, Any]]:
    """Generate time intervals for a full day."""
    pass
