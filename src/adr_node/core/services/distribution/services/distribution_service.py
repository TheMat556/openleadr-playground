from datetime import datetime, timezone
from threading import Event, Lock
from typing import Dict, List, Any, Optional
import numpy as np
from numpy.typing import NDArray
import time

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.services.distribution.interfaces.idistribution_service import (
  IDistributionService,
)
from src.adr_node.core.services.distribution.domain.distribution_parameters import (
  DistributionParameters,
)
from src.adr_node.core.services.distribution.domain.distribution_result import (
  DistributionResult,
)
from src.adr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.database.interfaces.services.iz_value_service import IZValueService
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus
from src.adr_node.event_bus.constants.signal_types import SignalType
from src.adr_node.event_bus.decorators.handle_signal import handle_signal
from src.adr_node.event_bus.decorators.init_signal_handlers import init_signal_handlers
from src.openadr_node import logger


class DistributionService(IDistributionService, IRunnable):
  """Service for managing load distribution calculations."""

  def __init__(
    self,
    consumption_service: IConsumptionService,
    load_profile_service: ILoadProfileService,
    z_value_service: IZValueService,
    parameters: DistributionParameters,
    event_bus: IEventBus,
  ):
    self._consumption_service = consumption_service
    self._load_profile_service = load_profile_service
    self._z_value_service = z_value_service
    self.event_bus = event_bus
    self._params = parameters
    self._z: Optional[float] = None
    self._stop_event = Event()
    self._is_running = False
    self._lock = Lock()
    self._force_recalculate = False
    init_signal_handlers(self)

  @handle_signal(SignalType.LOAD_PROFILE_UPDATED)
  def handle_load_profile_update(self, sender: str) -> None:
    """Handle load profile update signals."""
    logger.info(f'Load profile update received from {sender}')
    with self._lock:
      self._force_recalculate = True
      self._z = None

  def run(self) -> None:
    """Start the distribution service operations."""
    try:
      with self._lock:
        if self._is_running:
          logger.warning('Distribution service is already running')
          return
        self._is_running = True
        self._stop_event.clear()

      logger.info(
        f'Distribution service started at {datetime.now(timezone.utc).isoformat()}'
      )

      while not self._stop_event.is_set():
        try:
          force_update = False
          with self._lock:
            if self._force_recalculate:
              force_update = True
              self._force_recalculate = False

          current_time = int(time.time())
          print('current_time', current_time)
          consumption_result = self._consumption_service.get_closest_consumption_points(
            current_time,
            self._params.time_window_ms if self._params.time_window_ms else 900000,
          )
          print('consumption_result', consumption_result)

          if consumption_result.success and consumption_result.data:
            consumption_points = consumption_result.data.get('consumption_points', [])
            print('consumption_points', consumption_points)
            if consumption_points or force_update:
              ven_ids = np.array([point.ven_id for point in consumption_points])
              values = np.array([point.value for point in consumption_points])

              # Sum values for each unique VEN ID
              unique_vens, indices = np.unique(ven_ids, return_inverse=True)
              summed_values = np.zeros(len(unique_vens))
              np.add.at(summed_values, indices, values)

              result = self.update_load_distribution(
                ven_ids=unique_vens,
                consumption_values=summed_values,
                timestamp=current_time,
                force_update=force_update,
              )
              print('update_load_distribution - result', result)

              if not result.success:
                logger.warning(
                  f'Distribution update failed at {datetime.fromtimestamp(current_time / 1000).isoformat()}: '
                  f'{result.error}'
                )
              else:
                logger.info(
                  f'Distribution updated successfully for {len(unique_vens)} VENs at '
                  f'{datetime.fromtimestamp(current_time / 1000).isoformat()}'
                )

          time.sleep(30)

        except Exception as e:
          logger.error(f'Error in distribution service loop: {str(e)}')
          time.sleep(5)

    except Exception as e:
      logger.error(f'Fatal error in distribution service: {str(e)}')
    finally:
      with self._lock:
        self._is_running = False
      logger.info(
        f'Distribution service stopped at {datetime.now(timezone.utc).isoformat()}'
      )

  def stop(self) -> None:
    """Stop the distribution service."""
    logger.info('Distribution service stop requested')
    self._stop_event.set()

  def is_running(self) -> bool:
    """Check if the service is running."""
    with self._lock:
      return self._is_running

  def update_load_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    timestamp: int,
    force_update: bool = False,
  ) -> DistributionResult:
    """Calculate and update load distribution for given VENs."""
    try:
      if len(ven_ids) != len(consumption_values):
        raise ValueError(
          'Length mismatch between ven_ids and consumption_values arrays'
        )

      if len(ven_ids) == 0:
        return DistributionResult(
          success=False,
          timestamp=timestamp,
          error='No VENs provided for distribution calculation',
        )

      load_profile = self._load_profile_service.get_closest_load_point(timestamp)
      if not load_profile:
        return DistributionResult(
          success=False, timestamp=timestamp, error='No load profile data available'
        )

      if force_update:
        self._z = None

      z_result = None
      if self._z is None:
        z_result = self._z_value_service.get_latest_z_values(
          time_window_ms=self._params.time_window_ms
        )

        if z_result.success and z_result.data['z_values']:
          z_values = np.array([z.z_value for z in z_result.data['z_values']])
          self._z = np.mean(z_values)

      total_allowed = load_profile['signal_payload']
      new_z_values = self._calculate_distribution(
        ven_ids, consumption_values, total_allowed
      )

      save_result = self._z_value_service.save_z_values(
        ven_ids=ven_ids, z_values=new_z_values, timestamp=timestamp
      )
      self.event_bus.emit(SignalType.LOAD_DISTRIBUTION_UPDATED)

      if not save_result.success:
        logger.warning(f'Failed to save z-values: {save_result.error}')

      intervals = self._generate_time_intervals(timestamp)

      return DistributionResult(
        success=True,
        timestamp=timestamp,
        ven_ids=ven_ids,
        z_values=new_z_values,
        total_allowed=total_allowed,
        intervals=intervals,
        stats={
          'active_vens': len(ven_ids),
          'total_consumption': float(consumption_values.sum()),
          'average_consumption': float(consumption_values.mean()),
          'z_value_history': {
            'count': z_result.data['count'] if z_result and z_result.success else 0,
            'window_ms': self._params.time_window_ms,
            'save_success': save_result.success if save_result else False,
            'forced_update': force_update,
          },
        },
      )

    except Exception as e:
      logger.error(f'Failed to update load distribution: {str(e)}')
      return DistributionResult(success=False, timestamp=timestamp, error=str(e))

  def _calculate_distribution(
    self,
    ven_ids: NDArray[np.str_],
    consumption_values: NDArray[np.float64],
    total_allowed: float,
  ) -> NDArray[np.float64]:
    """Calculate load distribution using vectorized operations."""
    try:
      z = np.full_like(
        consumption_values,
        self._z if self._z is not None else total_allowed / len(ven_ids),
      )

      print('Step 1')
      print('z', z)
      print('consumption_values', consumption_values)
      print('total_allowed', total_allowed)

      with np.errstate(divide='ignore', invalid='ignore'):
        g = np.divide(
          z,
          consumption_values,
          out=np.zeros_like(z),
          where=consumption_values != 0,
        )
        g = np.nan_to_num(g)
        g = np.clip(g, 0, self._params.max_g_value)

      print('Step 2')

      correction = self._calculate_correction_factor(g)
      print('correction', correction)
      print('consumption_values', consumption_values)
      print('g', g)

      w = (1 - g) * consumption_values * correction
      w_total = np.sum(w)

      print('w', w)
      print('w_total', w_total)

      print('Step 3')

      z_neu = w / w_total * total_allowed if w_total > 0 else np.zeros_like(w)

      print('Step 4')

      self._z = float(np.mean(z_neu))

      return z_neu

    except Exception as e:
      logger.error(f'Distribution calculation failed: {str(e)}')
      raise

  def _calculate_correction_factor(self, g: NDArray[np.float64]) -> NDArray[np.float64]:
    """Calculate correction factor using configured parameters."""
    print('g', g)
    print('self._params.correction_factor_a', self._params.correction_factor_a)
    print('self._params.correction_factor_b', self._params.correction_factor_b)
    print('self._params.correction_factor_c', self._params.correction_factor_c)

    return (
      (self._params.correction_factor_a * np.square(g))
      / self._params.correction_factor_b
      - (self._params.correction_factor_a * g) / self._params.correction_factor_b
      + self._params.correction_factor_c
    )

  def _generate_time_intervals(self, base_timestamp: int) -> List[Dict[str, Any]]:
    """Generate time intervals based on configuration."""
    try:
      intervals = np.arange(
        base_timestamp,
        base_timestamp + 24 * 3600 * 1000,
        self._params.interval_duration_ms,
      )

      return [
        {
          'dstart': int(start),
          'duration': self._params.interval_duration_ms,
          'signal_payload': 0,
        }
        for start in intervals
      ]
    except Exception as e:
      logger.error(f'Failed to generate time intervals: {str(e)}')
      raise
