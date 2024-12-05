import logging

from pydispatch import dispatcher

from src.openadr_node.decorator.send_decorator import SendDispatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdrBaseConfig:
  def __init__(self):
    if hasattr(self, '_register_dispatcher'):
      dispatcher.connect(
        self._register_dispatcher, signal='register_dispatcher', sender=dispatcher.Any
      )
      logger.info("Connected _register_dispatcher to signal 'register_dispatcher'.")
    else:
      logger.warning('No _register_dispatcher method found to connect.')
    SendDispatcher.connect_all(self)

    self._ready = False
