import json
import logging
import asyncio
from typing import List, Any

from src.adr_node.communication.mqtt.interfaces.imqtt_publish_service import (
  IMQTTPublishService,
)
from src.adr_node.communication.mqtt.interfaces.imqtt_subscribe_service import (
  IMQTTSubscribeService,
)
from src.adr_node.communication.mqtt.services.mqtt_connection_service import (
  MQTTConnectionService,
)
from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.config.topic_config import TopicConfig, TopicType


class MQTTService(IRunnable):
  """
  Service for managing MQTT connections, publishing, and subscribing.

  Attributes
  ----------
  topic_configs : MQTTServiceConfig
      Configuration for the MQTT service.
  connection_handler : MQTTConnectionService
      Handler for the MQTT connection.
  publish_handler : IMQTTPublishService
      Handler for publishing messages.
  subscribe_handler : IMQTTSubscribeService
      Handler for subscribing to topics.
  _running : bool
      Indicates if the service is running.
  _publish_task : asyncio.Task
      Task for periodic publishing.
  _message_queue : asyncio.Queue
      Queue for incoming messages.

  Methods
  -------
  run() -> None
      Starts the MQTT service.
  stop() -> None
      Stops the MQTT service.
  """

  def __init__(
    self,
    topic_configs: List[TopicConfig],
    connection_handler: MQTTConnectionService,
    publish_handler: IMQTTPublishService,
    subscribe_handler: IMQTTSubscribeService,
  ):
    self.topic_configs = topic_configs
    self.connection_handler = connection_handler
    self.publish_handler = publish_handler
    self.subscribe_handler = subscribe_handler
    self._running = False
    self._publish_task = None
    self._message_queue = asyncio.Queue()

  async def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
    """
    Callback for handling incoming messages.

    Parameters
    ----------
    client : Any
        The client instance for this callback.
    userdata : Any
        The private user data as set in Client() or userdata_set().
    message : Any
        The message received from the broker.
    """
    try:
      payload = json.loads(message.payload.decode())
      await self._message_queue.put((message.topic, payload))
    except json.JSONDecodeError as e:
      logging.error(f'Invalid JSON in message on topic {message.topic}: {e}')
    except Exception as e:
      logging.error(f'Error queueing message: {e}')

  async def _message_processor(self):
    """Asynchronously process messages from the queue."""
    while self._running:
      try:
        topic, payload = await self._message_queue.get()
        await asyncio.get_event_loop().run_in_executor(
          None, self.subscribe_handler.handle_message, topic, payload
        )
        self._message_queue.task_done()
      except Exception as e:
        logging.error(f'Error processing queued message: {e}')
      await asyncio.sleep(0)  # Yield to other tasks

  async def _periodic_publisher(self):
    """Asynchronously handle periodic publishing."""
    while self._running:
      try:
        for topic_config in self.topic_configs:
          if topic_config.topic_type == TopicType.PUBLISH:
            await asyncio.get_event_loop().run_in_executor(
              None,
              self.publish_handler.handle_periodic_publish,
              topic_config.topic,
            )
        await asyncio.sleep(10)  # Wait between publish cycles
      except Exception as e:
        logging.error(f'Error in periodic publisher: {e}')

  def run(self) -> None:
    """Starts the MQTT service."""
    try:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

      self.connection_handler.connect()
      self._running = True

      self.connection_handler.client.on_message = (
        lambda client, userdata, message: asyncio.run_coroutine_threadsafe(
          self._on_message(client, userdata, message), loop
        )
      )

      for topic_config in self.topic_configs:
        if topic_config.topic_type == TopicType.SUBSCRIBE:
          self.subscribe_handler.subscribe(topic_config.topic)

      tasks = [
        loop.create_task(self._message_processor()),
        loop.create_task(self._periodic_publisher()),
      ]

      loop.run_until_complete(asyncio.gather(*tasks))

    except Exception as e:
      logging.error(f'Failed to start MQTT Service: {e}')
      self.stop()
      raise
    finally:
      loop.close()

  def stop(self) -> None:
    """Stops the MQTT service."""
    try:
      self._running = False
      self.connection_handler.disconnect()
      logging.info('MQTT Service stopped')
    except Exception as e:
      logging.error(f'Error stopping MQTT Service: {e}')
