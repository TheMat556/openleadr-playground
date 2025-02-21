from abc import ABC, abstractmethod
from typing import Any


class IMQTTPublishService(ABC):
  """
  Abstract base class for MQTT publish handlers.

  Methods
  -------
  publish(topic: str, payload: Any) -> None
      Publishes a message to a specific topic.
  handle_periodic_publish(topic: str) -> None
      Handles periodic publishing for a specific topic.
  """

  @abstractmethod
  def publish(self, topic: str, payload: Any) -> None:
    """
    Publishes a message to a specific topic.

    Parameters
    ----------
    topic : str
        The topic to publish the message to.
    payload : Any
        The message payload to publish.
    """
    pass

  @abstractmethod
  def handle_periodic_publish(self, topic: str) -> None:
    """
    Handles periodic publishing for a specific topic.

    Parameters
    ----------
    topic : str
        The topic for which to handle periodic publishing.
    """
    pass
