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
  """
  Service for managing slider values and their interpolations.

  :param slider_repository: Repository for storing slider values.
  :type slider_repository: Any
  :param event_bus: Event bus for emitting signals.
  :type event_bus: IEventBus
  :param num_sliders: Number of sliders.
  :type num_sliders: int
  :param timezone_offset: Timezone offset from UTC.
  :type timezone_offset: int
  :param minutes_interval: Interval in minutes for interpolation.
  :type minutes_interval: int
  :param default_value: Default value for sliders.
  :type default_value: int
  """

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
    """
    Load slider values from the repository.

    :return: A list of slider values.
    :rtype: List[int]
    """
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
    """
    Save slider values to the repository.

    :param values: The slider values to save.
    :type values: Any
    """
    try:
      self._current_values = values[: self.num_sliders]
      print('!!!!', self._current_values)
      self.repository.save(self._current_values)
      self._event_bus.emit(SignalType.LOAD_PROFILE_UPDATED)
    except Exception as e:
      self.logger.error(f'Error saving slider values: {e}')

  def interpolate_values(self, values: List[int]) -> Dict[str, np.ndarray]:
    """
    Interpolate hourly values to 15-minute intervals.

    :param values: A list of slider values.
    :type values: List[int]
    :return: A dictionary with interpolated values.
    :rtype: Dict[str, np.ndarray]
    """
    now = datetime.now(timezone.utc).astimezone(self.timezone)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    hourly_timestamps = np.array(
      [
        int((start_of_day + timedelta(hours=i)).timestamp())
        for i in range(self.num_sliders)
      ]
    )

    minute_timestamps = np.array(
      [
        int((start_of_day + timedelta(minutes=i * self.minutes_interval)).timestamp())
        for i in range(int(24 * 60 / self.minutes_interval))
      ]
    )

    values_array = np.array(values, dtype=float)
    interpolated_values = np.interp(minute_timestamps, hourly_timestamps, values_array)

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
    """
    Get current allowed consumption based on slider values.

    :return: The current allowed consumption.
    :rtype: float
    """
    now = datetime.now(timezone.utc).astimezone(self.timezone)
    interpolated_data = self.interpolate_values(self._current_values)

    minutes = now.minute
    rounded_minutes = (minutes // self.minutes_interval) * self.minutes_interval
    current_time = now.replace(minute=rounded_minutes, second=0, microsecond=0)
    current_timestamp = int(current_time.timestamp())

    idx = np.abs(interpolated_data['timestamps'] - current_timestamp).argmin()

    try:
      return float(interpolated_data['values'][idx])
    except IndexError:
      self.logger.warning(f'No value found for time {current_time}, using default')
      return float(self.default_value)

  def get_time_series_data(self) -> Dict[datetime, float]:
    """
    Get complete time series data for the current day.

    :return: A dictionary with time series data.
    :rtype: Dict[datetime, float]
    """
    interpolated_data = self.interpolate_values(self._current_values)

    times = [
      datetime.fromtimestamp(ts, tz=self.timezone)
      for ts in interpolated_data['timestamps']
    ]

    return dict(zip(times, interpolated_data['values']))
