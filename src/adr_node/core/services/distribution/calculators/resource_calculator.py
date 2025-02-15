from typing import Dict, Any, Optional, Tuple, List, Union

import logging
import numpy as np
from numpy.typing import NDArray
from ..interfaces.iresource_calculator import IResourceCalculator


class ResourceCalculator(IResourceCalculator):
  """
  Resource Calculator for the OpenADR system.

  This class provides methods to calculate load distribution and Z values
  for the ADR system.

  Attributes
  ----------
  CORRECTION_FACTOR_A : float
      Correction factor A.
  CORRECTION_FACTOR_B : float
      Correction factor B.
  CORRECTION_FACTOR_C : float
      Correction factor C.
  _z : Optional[Union[float, NDArray[np.float64]]]
      The Z value or array of Z values.
  """

  CORRECTION_FACTOR_A: float = 5.0
  CORRECTION_FACTOR_B: float = 1.5
  CORRECTION_FACTOR_C: float = 1.085

  def __init__(self):
    """
    Initialize the ResourceCalculator.
    """
    self._z: Optional[Union[float, NDArray[np.float64]]] = None

  def set_z_value(self, value: Optional[Union[float, NDArray[np.float64]]]) -> None:
    """
    Set the Z value.

    Parameters
    ----------
    value : Optional[Union[float, NDArray[np.float64]]]
        The Z value or array of Z values.
    """
    self._z = value

  def process_latest_z_values(
    self, latest_z_values: List[Dict[str, Any]], ven_ids: NDArray[np.str_]
  ) -> Optional[NDArray[np.float64]]:
    """
    Process the latest Z values.

    Parameters
    ----------
    latest_z_values : List[Dict[str, Any]]
        List of dictionaries containing VEN IDs and Z values.
    ven_ids : NDArray[np.str_]
        Array of VEN IDs.

    Returns
    -------
    Optional[NDArray[np.float64]]
        Array of Z values corresponding to the VEN IDs.
    """
    if not latest_z_values:
      return None

    try:
      z_map = {item['ven_id']: item['z_value'] for item in latest_z_values}
      return np.array([z_map.get(ven_id, 0.0) for ven_id in ven_ids])
    except Exception as e:
      logging.error(f'Failed to process Z values: {str(e)}')
      return None

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
        Tuple of VEN IDs and corresponding new Z values.
    """
    z = (
      np.full_like(consumption_values, self._z)
      if not isinstance(self._z, np.ndarray)
      or self._z.shape != consumption_values.shape
      else self._z
    )

    with np.errstate(divide='ignore', invalid='ignore'):
      g = np.divide(
        z, consumption_values, out=np.zeros_like(z), where=consumption_values != 0
      )
      g = np.nan_to_num(g)
      g = np.clip(g, 0, 0.8)

    w = (1 - g) * consumption_values * self._calculate_correction_factor(g)
    w_total = np.sum(w)
    z_neu = w / w_total * total_allowed if w_total > 0 else np.zeros_like(w)

    return ven_ids, z_neu

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
        Dictionary containing the current allowed consumption.
    active_vens_count : int
        Number of active VENs.
    pending_vens_count : int
        Number of pending VENs.

    Returns
    -------
    float
        The calculated Z value.
    """
    if active_vens_count < 0 or pending_vens_count < 0:
      raise ValueError('VEN counts cannot be negative')

    if active_vens_count == 0:
      total_ven_count = max(pending_vens_count + active_vens_count, 1)
      return current_allowed_consumption['signal_payload'] / total_ven_count

    if self._z is None:
      self._z = current_allowed_consumption['signal_payload'] / active_vens_count
    return float(self._z)

  def _calculate_correction_factor(self, g: NDArray[np.float64]) -> NDArray[np.float64]:
    """
    Calculate the correction factor.

    Parameters
    ----------
    g : NDArray[np.float64]
        Array of G values.

    Returns
    -------
    NDArray[np.float64]
        Array of correction factors.
    """
    return (
      (self.CORRECTION_FACTOR_A * np.square(g)) / self.CORRECTION_FACTOR_B
      - (self.CORRECTION_FACTOR_A * g) / self.CORRECTION_FACTOR_B
      + self.CORRECTION_FACTOR_C
    )
