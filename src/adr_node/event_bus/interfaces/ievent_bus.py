from abc import ABC, abstractmethod
from typing import Callable
from ..constants.signal_types import SignalType


class IEventBus(ABC):
  """Interface for event bus implementations."""

  @abstractmethod
  def subscribe(self, signal: SignalType, handler: Callable) -> None:
    """Subscribe to a signal."""
    pass

  @abstractmethod
  def unsubscribe(self, signal: SignalType, handler: Callable) -> None:
    """Unsubscribe from a signal."""
    pass

  @abstractmethod
  def emit(self, signal: SignalType) -> None:
    """Emit a signal."""
    pass
