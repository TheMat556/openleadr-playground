import logging

from pydispatch import dispatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdrBaseConfig:
  def __init__(self):
    self._ready = False
    self._deferred_signals = []

    # Connect to the `node_ready` event
    dispatcher.connect(self._on_node_ready, signal="node_ready", sender="vtn")

  def _on_node_ready(self, **kwargs):
    """
    Handle the `node_ready` event and process deferred signals.
    """
    logger.info("Node is ready. Processing deferred signals.")
    self._ready = True

    # Dispatch all deferred signals
    logger.debug(f"Deferred signals before dispatching: {self._deferred_signals}")
    for signal, sender, payload in self._deferred_signals:
      logger.info(f"Dispatching deferred signal: {signal} from sender: {sender}")
      dispatcher.send(signal=signal, sender=sender, **payload)

    # Clear the queue after dispatching
    self._deferred_signals.clear()
    logger.info(f"Deferred signals after clearing: {self._deferred_signals}")
