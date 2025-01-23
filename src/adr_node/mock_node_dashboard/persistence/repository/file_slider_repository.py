# src/persistence/repositories/file_slider_repository.py
from typing import List, Optional
import logging
from pathlib import Path
import threading

from src.adr_node.mock_node_dashboard.persistence.interfaces.slider_repository import (
  ISliderRepository,
)


class FileSliderRepository(ISliderRepository):
  def __init__(self, file_path: str):
    """
    Initialize the file-based slider repository.

    Args:
        file_path: Path to the file where slider values will be stored
    """
    self.file_path = Path(file_path)
    self._lock = threading.Lock()
    self.logger = logging.getLogger(__name__)

    # Ensure directory exists
    self.file_path.parent.mkdir(parents=True, exist_ok=True)

  def save(self, values: List[int]) -> None:
    """
    Save slider values to a file.

    Args:
        values: List of integer values to save

    Raises:
        IOError: If the file cannot be written
    """
    try:
      with self._lock:
        with self.file_path.open('w') as file:
          for value in values:
            file.write(f'{value}\n')
      self.logger.debug(f'Saved {len(values)} values to {self.file_path}')
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
