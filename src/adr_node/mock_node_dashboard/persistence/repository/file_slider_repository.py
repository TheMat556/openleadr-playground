from datetime import timedelta, datetime, timezone
from typing import List, Optional, Union, Any, Dict, Tuple
import logging
from pathlib import Path
import threading

import numpy as np

from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.mock_node_dashboard.persistence.interfaces.slider_repository import (
  ISliderRepository,
)


class FileSliderRepository(ISliderRepository):
  def __init__(self, file_path: str, load_profile_service: ILoadProfileService):
    """
    Initialize the file-based slider repository.

    Args:
        file_path: Path to the file where slider values will be stored
    """
    file_path = './data/slider_values.txt'
    self.file_path = Path(file_path).resolve()
    self._load_profile_service = load_profile_service
    self._lock = threading.Lock()
    self.logger = logging.getLogger(__name__)

    # Ensure directory exists
    self.file_path.parent.mkdir(parents=True, exist_ok=True)

  def _save_to_file(self, values: List[int]) -> None:
    """Save raw slider values to file."""
    try:
      with self._lock:
        with self.file_path.open('w') as file:
          for value in values:
            file.write(f'{value}\n')
      self.logger.debug(f'Saved {len(values)} values to {self.file_path}')
    except Exception as e:
      self.logger.error(f'Failed to save values to file: {e}')
      raise IOError(f'Failed to save values to file: {e}')

  def _create_time_points(self) -> Tuple[np.ndarray, np.ndarray, datetime]:
    """Create time points for interpolation."""
    current_time = datetime.now(
      timezone(timedelta(hours=1))
    )  # Use current timestamp with GMT+1
    start_of_day = current_time.replace(hour=0, minute=0, second=0, microsecond=0)

    x_hours = np.arange(24)  # Hours 0-23
    x_15min = np.linspace(0, 23, 96)  # 96 points (24 hours * 4 quarters)

    return x_hours, x_15min, start_of_day

  def _interpolate_values(
    self, raw_values: List[int], x_hours: np.ndarray, x_15min: np.ndarray
  ) -> np.ndarray:
    """Perform linear interpolation of values."""
    y_values = np.array(raw_values)
    return np.interp(x_15min, x_hours, y_values)

  def _create_load_profile_entry(self, timestamp: int, value: float) -> Dict[str, Any]:
    """
    Create a single load profile entry with the required fields.

    Args:
        timestamp: Unix timestamp for the interval start
        value: The power value for this interval

    Returns:
        Dict with the required fields for load profile
    """
    return {
      'dtstart': timestamp,  # Start time of the interval
      'duration': 900,  # Duration in seconds (15 minutes = 900 seconds)
      'signal_payload': value,  # The actual power value
    }

  def _create_load_profile_data(
    self, interpolated_values: np.ndarray, start_of_day: datetime
  ) -> List[Dict[str, Any]]:
    """
    Create load profile data from interpolated values.

    Args:
        interpolated_values: Array of interpolated power values
        start_of_day: Starting datetime for the profile

    Returns:
        List of load profile entries
    """
    load_profile_data = []

    for i, value in enumerate(interpolated_values):
      interval_time = start_of_day + timedelta(minutes=15 * i)
      entry = self._create_load_profile_entry(
        int(interval_time.timestamp()), float(value)
      )
      load_profile_data.append(entry)

    return load_profile_data

  def save(self, values: Union[Tuple[int, ...], List[int]]) -> None:
    """
    Save slider values to file and load profile service with 15-minute interpolation.

    Args:
        values: Tuple or List of integer values to save

    Raises:
        IOError: If the file cannot be written
    """
    try:
      # Convert tuple to list if needed
      values_list = list(values) if isinstance(values, tuple) else values

      # Save raw values to file
      self._save_to_file(values_list)

      # Create time points for interpolation
      x_hours, x_15min, start_of_day = self._create_time_points()

      # Perform interpolation
      interpolated_values = self._interpolate_values(values_list, x_hours, x_15min)

      # Create load profile data
      load_profile_data = self._create_load_profile_data(
        interpolated_values, start_of_day
      )

      # Save to load profile service
      print("Saving to load profile service", load_profile_data)
      result = self._load_profile_service.save_load_profile(load_profile_data)
      print("result", result)

      if result['failed'] > 0:
        self.logger.warning(
          f'Failed to save {result["failed"]} entries. Errors: {result["errors"]}'
        )

      self.logger.debug(
        f'Successfully saved {result["success"]} 15-minute intervals to load profile service'
      )

    except Exception as e:
      self.logger.error(f'Failed to save slider values: {e}')
      raise IOError(f'Failed to save slider values: {e}')

  def load(self) -> Optional[List[int]]:
    """
    Load slider values from file.

    Returns:
        List of integer values if successful, None if file doesn't exist

    Raises:
        IOError: If the file exists but cannot be read
    """
    if not self.exists():
      return None

    try:
      values = []
      with self._lock:
        with self.file_path.open('r') as file:
          for line in file:
            try:
              value = int(line.strip())
              values.append(value)
            except ValueError:
              self.logger.warning(f'Skipped invalid value in file: {line.strip()}')
      self.logger.debug(f'Loaded {len(values)} values from {self.file_path}')
      return values
    except Exception as e:
      self.logger.error(f'Failed to load slider values: {e}')
      raise IOError(f'Failed to load slider values: {e}')

  def exists(self) -> bool:
    """
    Check if the slider values file exists.

    Returns:
        True if file exists, False otherwise
    """
    return self.file_path.exists()

  def clear(self) -> None:
    """
    Clear all stored slider values by deleting the file.

    Raises:
        IOError: If the file cannot be deleted
    """
    try:
      with self._lock:
        if self.exists():
          self.file_path.unlink()
      self.logger.debug(f'Cleared slider values file: {self.file_path}')
    except Exception as e:
      self.logger.error(f'Failed to clear slider values: {e}')
      raise IOError(f'Failed to clear slider values: {e}')
