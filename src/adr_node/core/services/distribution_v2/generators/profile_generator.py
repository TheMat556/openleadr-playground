# src/adr_node/core/services/distribution/generators/profile_generator.py
from typing import Dict, List, Any, Tuple
import numpy as np
from numpy.typing import NDArray

from ..interfaces.iprofile_generator import IProfileGenerator


class ProfileGenerator(IProfileGenerator):
  def create_ven_profiles(
    self,
    ven_ids: NDArray[np.str_],
    z_values: NDArray[np.float64],
    intervals: List[Dict[str, Any]],
  ) -> Dict[str, List[Dict[str, Any]]]:
    if ven_ids.size == 0 or z_values.size == 0:
      raise ValueError('VEN IDs and Z values must not be empty')

    def build_profile(pair: Tuple[str, float]) -> Tuple[str, List[Dict[str, Any]]]:
      ven_id, z_value = pair
      return str(ven_id), [
        {**interval, 'signal_payload': float(z_value)} for interval in intervals
      ]

    return dict(map(build_profile, zip(ven_ids, z_values)))
