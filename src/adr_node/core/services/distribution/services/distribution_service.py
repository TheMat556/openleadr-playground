import logging
import time
from threading import Event, Lock
from typing import List

import numpy as np
from numpy.typing import NDArray

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.services.distribution.domain.distribution_parameters import (
  DistributionParameters,
)
from src.adr_node.core.services.distribution.interfaces.iresource_calculator import (
  IResourceCalculator,
)
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.database.interfaces.services.iz_value_service import IZValueService
from src.adr_node.database.interfaces.services.ih_load_profile_service import (
  IHLoadProfileService,
)
from src.adr_node.event_bus.constants.signal_types import SignalType
from src.adr_node.event_bus.decorators.handle_signal import handle_signal
from src.adr_node.event_bus.decorators.init_signal_handlers import init_signal_handlers
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus


class DistributionService(IRunnable):
  """
  Distribution Service for the OpenADR system.

  This class manages the distribution of load among VEN nodes based on load profile points.
  The allowed consumption is derived from a load profile record while the actual consumption data
  is obtained from the H-load profiles. Historical z-values are attempted to be used if available.

  New logic:
    • The consumption data is obtained from the complete H-load profiles.
    • Each VEN’s consumption point is the first interval value of its H-load profile.
    • The allowed consumption (signal_payload) is retrieved from the load profile service.
    • If historical z-values exist, they are used for the initial distribution;
      otherwise, a new z-value is calculated using split mechanics.
    • A new method, berechne_neue_leistung, calculates updated distribution based on allowed consumption V,
      measured consumption B, and previous Z values.
    • The calculated results are then converted into separate numpy arrays for ven_ids, z_values, and timestamps,
      and then inserted into the database (db1) via the z_value service.

  Note: The h_load_profile service is retained and used to derive the consumption points.
  """

  def __init__(
    self,
    resource_calculator: IResourceCalculator,
    load_profile_service: ILoadProfileService,
    z_value_service: IZValueService,
    h_load_profile_service: IHLoadProfileService,
    parameters: DistributionParameters,
    event_bus: IEventBus,
  ):
    self._calculator = resource_calculator
    self._load_profile_service = load_profile_service
    self._z_value_service = z_value_service
    self._h_load_profile_service = (
      h_load_profile_service  # KEEP h_load_profile service!
    )
    self._params = parameters
    self.event_bus = event_bus

    self._stop_event = Event()
    self._is_running = False
    self._lock = Lock()
    self._force_recalculate = False

    # Trigger an initial update.
    self.handle_load_profile_update('')
    init_signal_handlers(self)

  @handle_signal(SignalType.LOAD_PROFILE_UPDATED)
  def handle_load_profile_update(self, sender: str) -> None:
    """
    Handle load profile update signal; force recalculation.
    """
    with self._lock:
      self._force_recalculate = True
      self._calculator.set_z_value(None)
      print('Force update triggered.')

  def run(self) -> None:
    """
    Run the distribution service loop.
    Periodically retrieves consumption data from the H-load profiles (using the first interval per VEN),
    obtains the allowed consumption from the load profile service, calculates the new distribution,
    reshapes the results into separate numpy arrays, and inserts them into the database (db1)
    via the z_value service.
    """
    try:
      with self._lock:
        if self._is_running:
          return
        self._is_running = True
        self._stop_event.clear()

      while not self._stop_event.is_set():
        try:
          with self._lock:
            force_update = self._force_recalculate
            self._force_recalculate = False

          # Update distribution calculations (returns a list of records)
          distribution_results = self.update_load_distribution(force_update)

          # Convert the distribution_results into separate numpy arrays.
          if distribution_results:
            ven_ids_arr: NDArray[np.str_] = np.array(
              [record['ven_id'] for record in distribution_results],
              dtype=str,
            )
            z_values_arr: NDArray[np.float64] = np.array(
              [record['value'] for record in distribution_results],
              dtype=np.float64,
            )
            timestamps_arr: NDArray[np.int64] = np.array(
              [int(record['timestamp']) for record in distribution_results],
              dtype=np.int64,
            )
          else:
            ven_ids_arr = np.array([], dtype=str)
            z_values_arr = np.array([], dtype=np.float64)
            timestamps_arr = np.array([], dtype=np.int64)

          # Insert the results into the database using the z_value service.
          self._z_value_service.save_z_values(ven_ids_arr, z_values_arr, timestamps_arr)

          # Emit update signal.
          self.event_bus.emit(SignalType.LOAD_DISTRIBUTION_UPDATED)

          time.sleep(30)
        except Exception as e:
          logging.error(f'Error in distribution service loop: {str(e)}')
          time.sleep(5)
    finally:
      with self._lock:
        self._is_running = False

  def berechne_neue_leistung(self, V, B, prev_Z=None):
    """
    Calculate new power distribution (Z_new) based on allowed consumption V,
    measured consumption (B) and optional previous Z values.

    If no previous Z values exist, an equal initial distribution is applied.
    Returns a numpy array of new Z values.
    """
    n = len(B)
    if prev_Z is None or all(element is None for element in prev_Z):
      Z = np.full(n, V / n)  # Initial equal distribution
    else:
      Z = np.array(prev_Z)  # Use previous Z values

    # Calculate supply ratios G_i
    G = Z / B
    # Calculate correction factors K_i
    K = (5 * G**2) / 1.5 - (5 * G) / 1.5 + 1.085
    # Calculate weights W_i
    W = (1 - G) * B * K
    W_total = np.sum(W)
    # Compute new distribution Z_new
    Z_new = (W / W_total) * V

    # Redistribute surplus power if any VEN exceeds its measured consumption
    for i in range(n):
      if Z_new[i] > B[i]:
        surplus = Z_new[i] - B[i]
        Z_new[i] = B[i]
        under_limit = Z_new < B
        remaining_weight = np.sum(W[under_limit])
        if remaining_weight > 0:
          Z_new[under_limit] += (W[under_limit] / remaining_weight) * surplus
    return Z_new

  def update_load_distribution(self, force_update: bool = False) -> List[dict]:
    """
    Update load distribution for VEN nodes by iterating over timestamps from the H-load profile.

    For each timestamp (t) present in the H-load profile:
      - Retrieve the allowed consumption V from the load profile data (using key 'signal_payload')
        for that timestamp.
      - For each VEN, get its measured consumption B for that timestamp.
      - Compute new distribution values Z_new using berechne_neue_leistung.
      - Update previous Z and store each record in a list.

    Returns:
      A list of dictionaries, each with keys: "timestamp", "ven_id", "value".
    """
    load_profile = self._load_profile_service.get_load_profile_data()
    h_profile = self._h_load_profile_service.get_h_load_profile()

    # Expect h_profile to contain keys: "timestamp", "ven_ids", "value"
    timestamps = np.unique(h_profile['timestamp'])
    ven_ids = np.unique(h_profile['ven_ids'])

    distribution_results = []
    prev_Z_dict = {ven: None for ven in ven_ids}

    for t in timestamps:
      if t not in load_profile['dstart']:
        continue

      indices = np.where(load_profile['dstart'] == t)[0]
      if len(indices) == 0:
        logging.warning(f'No allowed consumption found for timestamp {t}')
        continue
      V = load_profile['signal_payload'][indices[0]]

      B = []
      for ven in ven_ids:
        idx = np.where((h_profile['timestamp'] == t) & (h_profile['ven_ids'] == ven))[0]
        if len(idx) == 0:
          logging.warning(f'No consumption value for VEN {ven} at timestamp {t}')
          B.append(0.0)
        else:
          B.append(float(h_profile['value'][idx[0]]))
      B = np.array(B, dtype=np.float64)

      prev_Z = [prev_Z_dict[ven] for ven in ven_ids]
      Z_new = self.berechne_neue_leistung(V, B, prev_Z)

      for i, ven in enumerate(ven_ids):
        prev_Z_dict[ven] = Z_new[i]
        distribution_results.append({'timestamp': t, 'ven_id': ven, 'value': Z_new[i]})

    return distribution_results

  def stop(self) -> None:
    """
    Stop the distribution service.
    """
    self._stop_event.set()

  def is_running(self) -> bool:
    """
    Check if the distribution service is running.
    """
    with self._lock:
      return self._is_running
