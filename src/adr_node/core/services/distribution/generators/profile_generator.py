from typing import Dict, List, Any, Tuple
import numpy as np
from numpy.typing import NDArray

from ..interfaces.iprofile_generator import IProfileGenerator


class ProfileGenerator(IProfileGenerator):
  """
  Profile Generator for the OpenADR system.

  This class provides methods to create VEN profiles based on Z values and intervals.

  Methods
  -------
  create_ven_profiles(ven_ids: NDArray[np.str_], z_values: NDArray[np.float64], intervals: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]
      Create profiles for the VENs.
  """

  def create_ven_profiles(
    self,
    ven_ids: NDArray[np.str_],
    z_values: NDArray[np.float64],
    intervals: List[Dict[str, Any]],
  ) -> Dict[str, List[Dict[str, Any]]]:
    """
    Create profiles for the VENs.

    Parameters
    ----------
    ven_ids : NDArray[np.str_]
        Array of VEN IDs.
    z_values : NDArray[np.float64]
        Array of Z values.
    intervals : List[Dict[str, Any]]
        List of intervals.

    Returns
    -------
    Dict[str, List[Dict[str, Any]]]
        Dictionary of VEN IDs and their corresponding profiles.
    """
    if ven_ids.size == 0 or z_values.size == 0:
      raise ValueError('VEN IDs and Z values must not be empty')

    def build_profile(pair: Tuple[str, float]) -> Tuple[str, List[Dict[str, Any]]]:
      ven_id, z_value = pair
      return str(ven_id), [
        {**interval, 'signal_payload': float(z_value)} for interval in intervals
      ]

    return dict(map(build_profile, zip(ven_ids, z_values)))
