from typing import Dict, Any, Callable, List, Union
import paho.mqtt.client as mqtt
from src.openadr_node import logger


class MQTTSubscriber:
  """Handles MQTT subscription operations for multiple topics."""

  def __init__(self, client: mqtt.Client) -> None:
    """
    Initialize the MQTT Subscriber.

    Parameters
    ----------
    client : mqtt.Client
        The MQTT client instance to use for subscriptions.
    """
    self.client = client
    self.topic_handlers: Dict[str, Callable] = {}
    print('TESTTSTST')

  def subscribe_with_handler(
    self,
    topics: Union[str, List[str]],
    handlers: Union[Callable[[str, Any], None], List[Callable[[str, Any], None]]],
    qos: int = 0,
  ) -> None:
    """
    Subscribe to topics and set up their handlers in one operation.

    Parameters
    ----------
    topics : Union[str, List[str]]
        Single topic string or list of topics to subscribe to.
    handlers : Union[Callable[[str, Any], None], List[Callable[[str, Any], None]]]
        Single handler function or list of handler functions corresponding to topics.
    qos : int, optional
        Quality of Service level (0, 1, or 2), by default 0.

    Raises
    ------
    ValueError
        If the number of topics and handlers don't match.
    Exception
        If subscription fails.
    """
    # Convert single topic/handler to list for uniform processing
    topic_list = [topics] if isinstance(topics, str) else topics
    handler_list = [handlers] if callable(handlers) else handlers

    print('topic_list', topic_list)
    print('handler_list', handler_list)

    # Validate input
    if len(topic_list) != len(handler_list):
      raise ValueError('Number of topics must match number of handlers')

    try:
      # Add handlers and subscribe to topics
      for topic, handler in zip(topic_list, handler_list):
        # Add handler
        self.topic_handlers[topic] = handler
        logger.debug(f'Added handler for topic: {topic}')

        # Subscribe to topic
        result = self.client.subscribe(topic, qos)
        if result[0] != mqtt.MQTT_ERR_SUCCESS:
          logger.error(
            f'Failed to subscribe to topic {topic}. Result code: {result[0]}'
          )
        else:
          logger.info(f'Successfully subscribed to topic: {topic}')

    except Exception as e:
      logger.error(f'Failed to set up subscription: {e}', exc_info=True)
      raise

  def handle_message(self, topic: str, payload: Any) -> None:
    """
    Process received message based on its topic.

    Parameters
    ----------
    topic : str
        The topic the message was received on.
    payload : Any
        The message payload.
    """
    try:
      if topic in self.topic_handlers:
        handler = self.topic_handlers[topic]
        handler(topic, payload)
        logger.debug(f'Handled message for topic {topic}')
      else:
        logger.info(f'Received message on unhandled topic {topic}: {payload}')
    except Exception as e:
      logger.error(f'Error handling message for topic {topic}: {e}', exc_info=True)
