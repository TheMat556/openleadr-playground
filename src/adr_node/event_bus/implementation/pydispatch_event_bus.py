from typing import Callable, Dict, Set
from pydispatch import dispatcher
import logging

from ..interfaces.ievent_bus import IEventBus
from ..constants.signal_types import SignalType

logger = logging.getLogger(__name__)


class PyDispatchEventBus(IEventBus):
  """PyDispatch implementation of the event bus."""

  def __init__(self):
    """
    Initialize the PyDispatchEventBus.
    """
    self._handlers: Dict[SignalType, Set[Callable]] = {}
    self._logger = logging.getLogger(__name__)

  def subscribe(self, signal: SignalType, handler: Callable) -> None:
    """
    Subscribe a handler to a signal.

    :param signal: The signal type to subscribe to.
    :type signal: SignalType
    :param handler: The handler function to be called when the signal is emitted.
    :type handler: Callable
    """
    try:
      dispatcher.connect(handler, signal=signal.name, sender=dispatcher.Any)
      if signal not in self._handlers:
        self._handlers[signal] = set()
      self._handlers[signal].add(handler)
      self._logger.debug(f'Handler {handler.__name__} subscribed to {signal.name}')
    except Exception as e:
      self._logger.error(f'Subscription failed for {signal.name}: {e}')
      raise

  def unsubscribe(self, signal: SignalType, handler: Callable) -> None:
    """
    Unsubscribe a handler from a signal.

    :param signal: The signal type to unsubscribe from.
    :type signal: SignalType
    :param handler: The handler function to be removed.
    :type handler: Callable
    """
    try:
      dispatcher.disconnect(handler, signal=signal.name, sender=dispatcher.Any)
      if signal in self._handlers:
        self._handlers[signal].discard(handler)
      self._logger.debug(f'Handler {handler.__name__} unsubscribed from {signal.name}')
    except Exception as e:
      self._logger.error(f'Unsubscription failed for {signal.name}: {e}')
      raise

  def emit(self, signal: SignalType) -> None:
    """
    Emit a signal to all subscribed handlers.

    :param signal: The signal type to emit.
    :type signal: SignalType
    """
    try:
      self._logger.info(f'Emitting signal: {signal.name}')
      dispatcher.send(signal=signal.name, sender=self)
    except Exception as e:
      self._logger.error(f'Signal emission failed for {signal.name}: {e}')
      raise
