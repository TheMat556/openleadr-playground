# src/core/services/slider_service_impl.py
from datetime import datetime, timezone, timedelta
import pandas as pd
from typing import List, Dict
import logging

from src.adr_node.mock_node_dashboard.core.interfaces.islider_service import (
  ISliderService,
)


class SliderService(ISliderService):
  def __init__(
    self,
    slider_repository,
    num_sliders: int = 24,
    timezone_offset: int = 1,
    minutes_interval: int = 15,
    default_value: int = 30,
  ):
    self.repository = slider_repository
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

  def save_values(self, values: List[int]) -> None:
    print("slider_values - save_values")
    try:
      self._current_values = values[: self.num_sliders]
      self.repository.save(self._current_values)
      # UPDATE SLIDER self.event_bus.publish("slider_values_updated", self._current_values)
    except Exception as e:
      self.logger.error(f'Error saving slider values: {e}')

  def interpolate_values(self, values: List[int]) -> pd.DataFrame:
    """Interpolate hourly values to 15-minute intervals"""
    now = datetime.now(self.timezone)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Create hourly time index
    hourly_index = pd.date_range(
      start=start_of_day, periods=self.num_sliders, freq='1H', tz=self.timezone
    )

    # Create 15-minute time index
    minute_index = pd.date_range(
      start=start_of_day,
      periods=int(24 * 60 / self.minutes_interval),
      freq=f'{self.minutes_interval}min',
      tz=self.timezone,
    )

    # Create DataFrame with hourly values
    df_hourly = pd.DataFrame({'value': values}, index=hourly_index)

    # Interpolate to 15-minute intervals
    df_interpolated = df_hourly.reindex(minute_index).interpolate(method='linear')

    # Add additional columns
    df_interpolated['unix_timestamp'] = df_interpolated.index.astype(int) // 10**6
    df_interpolated['display_time'] = df_interpolated.index.strftime('%H:%M')

    return df_interpolated

  def get_current_allowed_consumption(self) -> float:
    now = datetime.now(self.timezone)
    interpolated_df = self.interpolate_values(self._current_values)
    current_time = now.replace(second=0, microsecond=0)

    # Round to nearest 15-minute interval
    minutes = current_time.minute
    rounded_minutes = (minutes // self.minutes_interval) * self.minutes_interval
    current_time = current_time.replace(minute=rounded_minutes)

    try:
      return float(interpolated_df.loc[current_time, 'value'])
    except KeyError:
      self.logger.warning(f'No value found for time {current_time}, using default')
      return float(self.default_value)

  def get_time_series_data(self) -> Dict[datetime, float]:
    interpolated_df = self.interpolate_values(self._current_values)
    return {index: row['value'] for index, row in interpolated_df.iterrows()}
