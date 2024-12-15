from pydispatch import dispatcher

from src.openadr_node import logger
from src.openadr_node.decorator.signal_sender import SignalSender


class AdrBaseConfig:
  def __init__(self) -> None:
    if hasattr(self, '_register_dispatcher'):
      dispatcher.connect(
        self._register_dispatcher, signal='register_dispatcher', sender=dispatcher.Any
      )
      logger.info("Connected _register_dispatcher to signal 'register_dispatcher'.")
    else:
      logger.warning('No _register_dispatcher method found to connect.')
    SignalSender.connect_all(self)

    self._ready: bool = False
