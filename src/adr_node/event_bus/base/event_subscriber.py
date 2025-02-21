from typing import Dict, Set
from ..interfaces.ievent_bus import IEventBus
from ..constants.signal_types import SignalType
import logging

logger = logging.getLogger(__name__)


class EventSubscriber:
  """
  Base class for classes that need to subscribe to events.
  Automatically registers methods decorated with @subscribes_to.
  """

  def __init__(self, event_bus: IEventBus):
    self.event_bus = event_bus
    self._registered_handlers: Dict[SignalType, Set[str]] = {}
    self._register_handlers()

  def _register_handlers(self) -> None:
    """Register all methods decorated with @subscribes_to."""
    for attr_name in dir(self):
      method = getattr(self, attr_name)
      if hasattr(method, '_signal_subscription'):
        signal_type = method._signal_subscription
        self.event_bus.subscribe(signal_type, method)

        if signal_type not in self._registered_handlers:
          self._registered_handlers[signal_type] = set()
        self._registered_handlers[signal_type].add(attr_name)

        logger.debug(f'Registered handler {attr_name} for signal {signal_type.name}')

  def __del__(self):
    """Cleanup by unsubscribing all handlers."""
    for signal_type, handlers in self._registered_handlers.items():
      for handler_name in handlers:
        handler = getattr(self, handler_name)
        self.event_bus.unsubscribe(signal_type, handler)
