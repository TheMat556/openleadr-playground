from functools import wraps
from typing import Callable
import logging
from ..constants.signal_types import SignalType

logger = logging.getLogger(__name__)


def emits_signal(signal_type: SignalType):
  """
  Decorator to emit a signal when a method completes successfully.

  Usage:
      @emits_signal(SignalType.CONSUMPTION_READY)
      def process_data(self):
          pass
  """

  def decorator(func: Callable):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
      try:
        result = func(self, *args, **kwargs)
        if hasattr(self, 'event_bus'):
          self.event_bus.emit(signal_type)
        return result
      except Exception as e:
        if hasattr(self, 'event_bus'):
          self.event_bus.emit(SignalType.ERROR_OCCURRED)
        raise e

    return wrapper

  return decorator
