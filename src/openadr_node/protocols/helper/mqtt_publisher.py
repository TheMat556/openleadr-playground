from typing import Any
import paho.mqtt.client as mqtt
from src.openadr_node import logger


class MQTTPublisher:
  """Handles MQTT publishing operations."""

  def __init__(self, client: mqtt.Client) -> None:
    """
    Initialize the MQTTPublisher.

    Parameters
    ----------
    client : mqtt.Client
        The MQTT client instance to use for publishing.
    """
    self.client = client

  def publish(self, topic: str, payload: Any, qos: int = 0) -> None:
    """
    Publish a message to a specific topic.

    Parameters
    ----------
    topic : str
        The topic to publish to.
    payload : Any
        The message payload.
    qos : int, optional
        Quality of Service level (0, 1, or 2), by default 0.

    Raises
    ------
    Exception
        If publishing the message fails.
    """
    try:
      self.client.publish(topic, payload, qos=qos)
      logger.debug(f'Published message to {topic}: {payload}')
    except Exception as e:
      logger.error(f'Failed to publish message: {e}', exc_info=True)
      raise
