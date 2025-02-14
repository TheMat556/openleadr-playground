from threading import Event, Lock
from typing import List
import time

import logging
import numpy as np

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.services.distribution.domain.distribution_parameters import (
  DistributionParameters,
)
from src.adr_node.core.services.distribution_v2.domain.distribution_result import (
  DistributionResult,
)
from src.adr_node.core.services.distribution_v2.interfaces.iprofile_generator import (
  IProfileGenerator,
)
from src.adr_node.core.services.distribution_v2.interfaces.iresource_calculator import (
  IResourceCalculator,
)
from src.adr_node.core.services.distribution_v2.interfaces.itime_interval_generator import (
  ITimeIntervalGenerator,
)
from src.adr_node.database.domain.data.consumption_data import ConsumptionData
from src.adr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.database.interfaces.services.iz_value_service import IZValueService
from src.adr_node.event_bus.constants.signal_types import SignalType
from src.adr_node.event_bus.decorators.handle_signal import handle_signal
from src.adr_node.event_bus.decorators.init_signal_handlers import init_signal_handlers
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus


class DistributionService(IRunnable):
  def __init__(
    self,
    resource_calculator: IResourceCalculator,
    time_interval_generator: ITimeIntervalGenerator,
    profile_generator: IProfileGenerator,
    consumption_service: IConsumptionService,
    load_profile_service: ILoadProfileService,
    z_value_service: IZValueService,
    parameters: DistributionParameters,
    event_bus: IEventBus,
  ):
    self._calculator = resource_calculator
    self._interval_generator = time_interval_generator
    self._profile_generator = profile_generator
    self._consumption_service = consumption_service
    self._load_profile_service = load_profile_service
    self._z_value_service = z_value_service
    self._params = parameters
    self.event_bus = event_bus
    self._stop_event = Event()
    self._is_running = False
    self._lock = Lock()
    self._force_recalculate = False
    self.handle_load_profile_update('')
    init_signal_handlers(self)

  @handle_signal(SignalType.LOAD_PROFILE_UPDATED)
  def handle_load_profile_update(self, sender: str) -> None:
    print('!!handle_load_profile_update!!')
    with self._lock:
      self._force_recalculate = True
      self._calculator.set_z_value(None)

  def run(self) -> None:
    try:
      with self._lock:
        if self._is_running:
          return
        self._is_running = True
        self._stop_event.clear()

      while not self._stop_event.is_set():
        try:
          force_update = False
          with self._lock:
            if self._force_recalculate:
              force_update = True
              self._force_recalculate = False

          current_time = int(time.time() * 1000)
          consumption_result = self._consumption_service.get_closest_consumption_points(
            current_time, self._params.time_window_ms
          )

          if consumption_result.success and consumption_result.data:
            self.update_load_distribution(
              consumption_result.data.get('consumption_points', []),
              current_time,
              force_update,
            )

          time.sleep(30)

        except Exception as e:
          logging.error(f'Error in distribution service loop: {str(e)}')
          time.sleep(5)

    finally:
      with self._lock:
        self._is_running = False

  def update_load_distribution(
    self,
    consumption_points: List[ConsumptionData],
    timestamp: int,
    force_update: bool = False,
  ) -> DistributionResult:
    """
    Update load distribution for VEN nodes.

    Args:
        consumption_points: List of consumption data points
        timestamp: Current timestamp in milliseconds
        force_update: Flag to force recalculation

    Returns:
        DistributionResult containing the calculation results
    """
    try:
      if not consumption_points:
        return DistributionResult(
          success=False, timestamp=timestamp, error='No consumption points provided'
        )

      print('!!!STEP 1!!!')
      load_profile = self._load_profile_service.get_closest_load_point(timestamp)
      print('load_profile', load_profile)

      if not load_profile:
        return DistributionResult(
          success=False, timestamp=timestamp, error='No load profile data available'
        )

      if force_update:
        self._calculator.set_z_value(None)

      # Process consumption data
      ven_data = [(point.ven_id, point.value) for point in consumption_points]
      ven_ids = np.array([x[0] for x in ven_data], dtype=str)
      consumption_values = np.array([x[1] for x in ven_data], dtype=np.float64)

      print('!!!STEP 2!!!')
      print('Processing z-values')

      # Initial z-value calculation
      if self._calculator._z is None:
        z_result = self._z_value_service.get_latest_z_values(
          time_window_ms=self._params.time_window_ms
        )
        print('z_result', z_result)

        # Try to use historical z-values first
        if z_result.success and z_result.data.get('z_values'):
          processed_z_values = self._calculator.process_latest_z_values(
            z_result.data['z_values'], ven_ids
          )
          if processed_z_values is not None:
            self._calculator.set_z_value(processed_z_values)

        # Calculate new z-value if no history available
        else:
          print('Calculating new z-value')
          active_vens = len(ven_ids)
          pending_vens = 0
          z_value = self._calculator.calculate_z_value(
            load_profile, active_vens, pending_vens
          )
          print(f'Calculated z-value: {z_value}')

          # Set and use initial z-value
          self._calculator.set_z_value(z_value)
          z_values = np.full_like(consumption_values, z_value)

          # Generate initial profiles
          intervals = self._interval_generator.generate_intervals()
          profiles = self._profile_generator.create_ven_profiles(
            ven_ids, z_values, intervals
          )

          # Save initial z-values
          save_result = self._z_value_service.save_z_values(
            ven_ids=ven_ids, z_values=z_values, timestamp=timestamp
          )

          # Notify about initial update
          self.event_bus.emit(SignalType.LOAD_DISTRIBUTION_UPDATED)

          # Return initial distribution result
          return DistributionResult(
            success=True,
            timestamp=timestamp,
            ven_ids=ven_ids,
            z_values=z_values,
            total_allowed=load_profile['signal_payload'],
            profiles=profiles,
            intervals=intervals,
            stats={
              'active_vens': active_vens,
              'total_consumption': float(consumption_values.sum()),
              'average_consumption': float(consumption_values.mean()),
              'z_value_history': {
                'count': 0,
                'window_ms': self._params.time_window_ms,
                'save_success': save_result.success
                if 'save_result' in locals()
                else False,
                'forced_update': force_update,
              },
            },
          )

      print('!!!STEP 3!!!')
      print(f'Current z-value: {self._calculator._z}')

      # Regular distribution calculation
      total_allowed = load_profile['signal_payload']
      ven_ids, z_values = self._calculator.calculate_load_distribution(
        ven_ids, consumption_values, total_allowed
      )

      print('!!!STEP 4!!!')

      # Save calculated results
      save_result = self._z_value_service.save_z_values(
        ven_ids=ven_ids, z_values=z_values, timestamp=timestamp
      )

      print('!!!STEP 5!!!')

      # Generate profiles
      intervals = self._interval_generator.generate_intervals()
      profiles = self._profile_generator.create_ven_profiles(
        ven_ids, z_values, intervals
      )

      # Notify about update
      self.event_bus.emit(SignalType.LOAD_DISTRIBUTION_UPDATED)

      # Return final distribution result
      return DistributionResult(
        success=True,
        timestamp=timestamp,
        ven_ids=ven_ids,
        z_values=z_values,
        total_allowed=total_allowed,
        profiles=profiles,
        intervals=intervals,
        stats={
          'active_vens': len(ven_ids),
          'total_consumption': float(consumption_values.sum()),
          'average_consumption': float(consumption_values.mean()),
          'z_value_history': {
            'count': z_result.data['count']
            if 'z_result' in locals() and z_result.success
            else 0,
            'window_ms': self._params.time_window_ms,
            'save_success': save_result.success if 'save_result' in locals() else False,
            'forced_update': force_update,
          },
        },
      )

    except Exception as e:
      logging.error(f'Failed to update load distribution: {str(e)}')
      return DistributionResult(success=False, timestamp=timestamp, error=str(e))

  def stop(self) -> None:
    self._stop_event.set()

  def is_running(self) -> bool:
    with self._lock:
      return self._is_running
