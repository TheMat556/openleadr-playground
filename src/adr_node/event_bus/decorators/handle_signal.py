from functools import wraps
from typing import Callable
import logging
from ..constants.signal_types import SignalType

logger = logging.getLogger(__name__)


def handle_signal(signal_type: SignalType):
  """
  Decorator that automatically subscribes a method to a signal when the class is instantiated.

  Usage:
      @handle_signal(SignalType.CONSUMPTION_READY)
      def on_consumption_ready(self, sender):
          pass
  """

  def decorator(func: Callable):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
      # Extract sender from kwargs if present
      sender = kwargs.pop('sender', args[0] if args else None)
      # Extract signal from kwargs if present
      kwargs.pop('signal', None)

      logger.debug(f'Signal handler {func.__name__} called with sender {sender}')
      return func(self, sender)

    # Mark the function as a signal handler
    wrapper._is_signal_handler = True
    wrapper._signal_type = signal_type

    return wrapper

  return decorator
