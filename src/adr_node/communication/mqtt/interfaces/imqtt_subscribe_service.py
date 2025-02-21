from abc import ABC, abstractmethod
from typing import Any


class IMQTTSubscribeService(ABC):
  """
  Abstract base class for MQTT subscribe handlers.

  Methods
  -------
  subscribe(topic: str) -> None
      Subscribes to a specific topic.
  handle_message(topic: str, payload: Any) -> None
      Handles incoming messages for a specific topic.
  """

  @abstractmethod
  def subscribe(self, topic: str) -> None:
    """
    Subscribes to a specific topic.

    Parameters
    ----------
    topic : str
        The topic to subscribe to.
    """
    pass

  @abstractmethod
  def handle_message(self, topic: str, payload: Any) -> None:
    """
    Handles incoming messages for a specific topic.

    Parameters
    ----------
    topic : str
        The topic for which to handle incoming messages.
    payload : Any
        The message payload received.
    """
    pass
