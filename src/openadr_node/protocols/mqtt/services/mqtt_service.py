# protocols/mqtt/services/mqtt_service.py
import json
from typing import Dict, Any

from src.openadr_node import logger
from ..config.mqtt_config import MQTTConfig
from ..interfaces.mqtt_interface import IMessageHandler, IMQTTClient


class MQTTService:
  def __init__(
    self,
    config: MQTTConfig,
    client: IMQTTClient,
    message_handlers: Dict[str, IMessageHandler],
  ):
    self.config = config
    self._client = client
    self._message_handlers = message_handlers
    self._running = False

  async def start(self) -> None:
    """Start the MQTT service"""
    try:
      await self._client.connect()
      self._running = True

      # Subscribe to topics
      for topic in self._message_handlers.keys():
        await self._client.subscribe(topic)

    except Exception as e:
      logger.error(f'Failed to start MQTT service: {e}')
      raise

  async def stop(self) -> None:
    """Stop the MQTT service"""
    try:
      self._running = False
      await self._client.disconnect()
    except Exception as e:
      logger.error(f'Failed to stop MQTT service: {e}')
      raise

  async def publish_load_profile(self, payload: Dict[str, Any]) -> None:
    """Publish load profile data"""
    try:
      if not self._running:
        raise RuntimeError('MQTT service is not running')

      await self._client.publish(self.config.topic_load_profile, json.dumps(payload))
    except Exception as e:
      logger.error(f'Failed to publish load profile: {e}')
      raise
