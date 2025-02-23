from typing import List, Dict, Any, Optional

import numpy as np
from datetime import datetime, timedelta, timezone

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.services.h_profile.interfaces.ih_profile_generator import (
  IHProfileGenerator,
)
from src.adr_node.database.interfaces.services.ih_load_profile_service import (
  IHLoadProfileService,
)
import random
import logging
from threading import Event

from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus


class HProfileGenerator(IHProfileGenerator, IRunnable):
  """Generates H-load profiles based on the Fourier series formula."""

  def __init__(
    self, h_load_profile_service: IHLoadProfileService, event_bus: IEventBus
  ):
    self.base_value = 117.2490
    self.coefficients = {
      1: (-25.7462, -31.0752),
      2: (4.9952, -35.8946),
      3: (-3.9014, -8.4675),
      4: (-2.7628, 7.7519),
      5: (-2.7861, -5.5456),
    }
    self.h_load_profile_service = h_load_profile_service
    self._stop_event = Event()
    self._event_bus = event_bus

  def generate_profile(self, t: float) -> float:
    """Generate a single H-profile value for time t."""
    result = self.base_value

    for n, (cos_coef, sin_coef) in self.coefficients.items():
      angle = 2 * np.pi * n * t / 96
      result += cos_coef * np.cos(angle) + sin_coef * np.sin(angle)

    random_multiplier = random.uniform(2.5, 3.5)
    return (result * random_multiplier) / 1000

  def generate_profile_batch(self, t_values: np.ndarray) -> np.ndarray:
    """Generate H-profile values for multiple time points."""
    results = np.full_like(t_values, self.base_value, dtype=float)

    for n, (cos_coef, sin_coef) in self.coefficients.items():
      angle = 2 * np.pi * n * t_values / 96
      results += cos_coef * np.cos(angle) + sin_coef * np.sin(angle)

    random_multipliers = np.random.uniform(2.5, 3.5, size=len(t_values))
    return results * random_multipliers

  def generate_daily_profile(
    self, start_datetime: datetime, ven_id: Optional[str] = None
  ) -> List[Dict[str, Any]]:
    """
    Generate a complete daily profile with 96 points (15-minute intervals).

    Args:
        start_datetime: The start time for the daily profile
        ven_id: Optional VEN ID to associate with the profile

    Returns:
        List of dictionaries containing timestamps and values
    """
    t_values = np.arange(96)
    values = self.generate_profile_batch(t_values)

    profile_data = []
    for i, value in enumerate(values):
      point_time = start_datetime + timedelta(minutes=15 * i)

      data_point = {
        'timestamp': int(point_time.timestamp()),
        'value': float(value),
      }
      if ven_id is not None:
        data_point['ven_id'] = ven_id

      profile_data.append(data_point)

    return profile_data

  def run(self):
    """Main run loop for generating and saving daily profiles."""
    logging.info('Starting H-profile generation loop')

    while not self._stop_event.is_set():
      try:
        # Get current time and round to previous midnight
        current_time = datetime.now(timezone.utc)
        start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # Generate base profile (without VEN ID)
        profile_data = self.generate_daily_profile(start_of_day)

        # Save to database with no VEN ID (base profile)
        result = self.h_load_profile_service.save_h_load_profile(
          profile_data,
          ven_id=None,  # Explicitly set to None for base profile
        )

        if result['failed'] > 0:
          logging.error(f'Failed to save H-profile data: {result["errors"]}')
        else:
          logging.info(
            f'Successfully generated and saved {len(profile_data)} H-profile points'
          )

        # Calculate time until next day
        next_day = start_of_day + timedelta(days=1)
        sleep_seconds = (next_day - datetime.now(timezone.utc)).total_seconds()

        # Wait until next day or until stopped
        self._stop_event.wait(max(0, sleep_seconds))

      except Exception as e:
        logging.error(f'Error in H-profile generation loop: {str(e)}')
        self._stop_event.wait(60)  # Wait 1 minute before retrying
