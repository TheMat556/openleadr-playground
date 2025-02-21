# src/persistence/interfaces/slider_repository.py
from abc import ABC, abstractmethod
from typing import List, Optional


class ISliderRepository(ABC):
  @abstractmethod
  def save(self, values: List[int]) -> None:
    """
    Save a list of slider values to persistent storage.

    Args:
        values: List of integer values to save

    Raises:
        IOError: If the values cannot be saved
    """
    pass

  @abstractmethod
  def load(self) -> Optional[List[int]]:
    """
    Load slider values from persistent storage.

    Returns:
        List of integer values if successful, None if no values exist

    Raises:
        IOError: If the values cannot be loaded
    """
    pass

  @abstractmethod
  def exists(self) -> bool:
    """
    Check if slider values exist in persistent storage.

    Returns:
        True if values exist, False otherwise
    """
    pass

  @abstractmethod
  def clear(self) -> None:
    """
    Clear all stored slider values.

    Raises:
        IOError: If the values cannot be cleared
    """
    pass
