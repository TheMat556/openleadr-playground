from abc import ABC, abstractmethod
from typing import Dict, Any


class IMQTTController(ABC):
  @abstractmethod
  def start(self) -> None:
    pass

  @abstractmethod
  def stop(self) -> None:
    pass

  @abstractmethod
  def publish_load_profile(self) -> None:
    pass


class IMessageHandler(ABC):
  @abstractmethod
  async def handle_message(self, topic: str, payload: Dict[str, Any]) -> None:
    """Handle incoming MQTT messages"""
    pass


class IMQTTClient(ABC):
  @abstractmethod
  async def connect(self) -> None:
    pass

  @abstractmethod
  async def disconnect(self) -> None:
    pass

  @abstractmethod
  async def publish(self, topic: str, payload: str) -> None:
    pass

  @abstractmethod
  async def subscribe(self, topic: str) -> None:
    pass
