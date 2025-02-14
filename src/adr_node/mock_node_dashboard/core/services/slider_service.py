from datetime import datetime, timezone, timedelta
import numpy as np
from typing import List, Dict, Any
import logging

from src.adr_node.event_bus.constants.signal_types import SignalType
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus
from src.adr_node.mock_node_dashboard.core.interfaces.islider_service import (
  ISliderService,
)


class SliderService(ISliderService):
  def __init__(
    self,
    slider_repository,
    event_bus: IEventBus,
    num_sliders: int = 24,
    timezone_offset: int = 1,
    minutes_interval: int = 15,
    default_value: int = 30,
  ):
    self.repository = slider_repository
    self._event_bus = event_bus
    self.num_sliders = num_sliders
    self.timezone = timezone(timedelta(hours=timezone_offset))
    self.minutes_interval = minutes_interval
    self.default_value = default_value
    self.logger = logging.getLogger(__name__)
    self._current_values = self.load_values()

  def load_values(self) -> List[int]:
    try:
      values = self.repository.load()
      if not values:
        values = [self.default_value] * self.num_sliders
      elif len(values) < self.num_sliders:
        values.extend([self.default_value] * (self.num_sliders - len(values)))
      return values[: self.num_sliders]
    except Exception as e:
      self.logger.error(f'Error loading slider values: {e}')
      return [self.default_value] * self.num_sliders

  def save_values(self, *values: Any) -> None:
    try:
      self._current_values = values[: self.num_sliders]
      self.repository.save(self._current_values)
      self._event_bus.emit(SignalType.LOAD_PROFILE_UPDATED)
    except Exception as e:
      self.logger.error(f'Error saving slider values: {e}')

  def interpolate_values(self, values: List[int]) -> Dict[str, np.ndarray]:
    """Interpolate hourly values to 15-minute intervals"""
    # Using the provided UTC time: 2025-02-08 22:59:19
    now = datetime.now(timezone.utc).astimezone(self.timezone)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Create hourly timestamps (24 points)
    hourly_timestamps = np.array(
      [
        int((start_of_day + timedelta(hours=i)).timestamp())
        for i in range(self.num_sliders)
      ]
    )

    # Create 15-minute timestamps (96 points)
    minute_timestamps = np.array(
      [
        int((start_of_day + timedelta(minutes=i * self.minutes_interval)).timestamp())
        for i in range(int(24 * 60 / self.minutes_interval))
      ]
    )

    # Convert values to numpy array
    values_array = np.array(values, dtype=float)

    # Interpolate values
    interpolated_values = np.interp(minute_timestamps, hourly_timestamps, values_array)

    # Generate display times
    display_times = np.array(
      [
        (start_of_day + timedelta(minutes=i * self.minutes_interval)).strftime('%H:%M')
        for i in range(int(24 * 60 / self.minutes_interval))
      ]
    )

    return {
      'timestamps': minute_timestamps,
      'values': interpolated_values,
      'display_times': display_times,
    }

  def get_current_allowed_consumption(self) -> float:
    # Using the provided UTC time: 2025-02-08 22:59:19
    now = datetime.now(timezone.utc).astimezone(self.timezone)
    interpolated_data = self.interpolate_values(self._current_values)

    # Round current time to nearest 15-minute interval
    minutes = now.minute
    rounded_minutes = (minutes // self.minutes_interval) * self.minutes_interval
    current_time = now.replace(minute=rounded_minutes, second=0, microsecond=0)
    current_timestamp = int(current_time.timestamp())

    # Find the closest timestamp index
    idx = np.abs(interpolated_data['timestamps'] - current_timestamp).argmin()

    try:
      return float(interpolated_data['values'][idx])
    except IndexError:
      self.logger.warning(f'No value found for time {current_time}, using default')
      return float(self.default_value)

  def get_time_series_data(self) -> Dict[datetime, float]:
    interpolated_data = self.interpolate_values(self._current_values)

    # Create datetime objects from timestamps
    times = [
      datetime.fromtimestamp(ts, tz=self.timezone)
      for ts in interpolated_data['timestamps']
    ]

    return dict(zip(times, interpolated_data['values']))
