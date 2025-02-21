from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, Union, List
import numpy as np
from numpy.typing import NDArray


class IResourceCalculator(ABC):
  """
  Interface for Resource Calculator in the OpenADR system.

  This interface defines methods to set Z values, calculate load distribution, calculate Z values, and process the latest Z values.

  Methods
  -------
  set_z_value(value: Optional[Union[float, NDArray[np.float64]]]) -> None
      Set the Z value.
  calculate_load_distribution(ven_ids: NDArray[np.str_], consumption_values: NDArray[np.float64], total_allowed: float) -> Tuple[NDArray[np.str_], NDArray[np.float64]]
      Calculate the load distribution.
  calculate_z_value(current_allowed_consumption: Dict[str, Any], active_vens_count: int, pending_vens_count: int) -> float
      Calculate the Z value.
  process_latest_z_values(latest_z_values: List[Dict[str, Any]], ven_ids: NDArray[np.str_]) -> Optional[NDArray[np.float64]]
      Process the latest Z values.
  """

  @abstractmethod
  def set_z_value(self, value: Optional[Union[float, NDArray[np.float64]]]) -> None:
    """
    Set the Z value.

    Parameters
    ----------
    value : Optional[Union[float, NDArray[np.float64]]]
        The Z value to set.
    """
    pass

  @abstractmethod
  def calculate_load_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    total_allowed: float,
  ) -> Tuple[NDArray[np.str_], NDArray[np.float64]]:
    """
    Calculate the load distribution.

    Parameters
    ----------
    ven_ids : NDArray[np.str_]
        Array of VEN IDs.
    consumption_values : NDArray[np.float64]
        Array of consumption values.
    total_allowed : float
        Total allowed consumption.

    Returns
    -------
    Tuple[NDArray[np.str_], NDArray[np.float64]]
        Tuple of VEN IDs and their corresponding load distribution values.
    """
    pass

  @abstractmethod
  def calculate_z_value(
    self,
    current_allowed_consumption: Dict[str, Any],
    active_vens_count: int,
    pending_vens_count: int,
  ) -> float:
    """
    Calculate the Z value.

    Parameters
    ----------
    current_allowed_consumption : Dict[str, Any]
        Current allowed consumption data.
    active_vens_count : int
        Count of active VENs.
    pending_vens_count : int
        Count of pending VENs.

    Returns
    -------
    float
        Calculated Z value.
    """
    pass

  @abstractmethod
  def process_latest_z_values(
    self, latest_z_values: List[Dict[str, Any]], ven_ids: NDArray[np.str_]
  ) -> Optional[NDArray[np.float64]]:
    """
    Process the latest Z values.

    Parameters
    ----------
    latest_z_values : List[Dict[str, Any]]
        List of latest Z values.
    ven_ids : NDArray[np.str_]
        Array of VEN IDs.

    Returns
    -------
    Optional[NDArray[np.float64]]
        Processed Z values.
    """
    pass
