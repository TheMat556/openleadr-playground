import asyncio
import json
import time
from typing import Any
import numpy as np
from threading import Event

from src.openadr_node import logger
from .helper.base_mqtt import BaseMQTT
from .helper.mqtt_publisher import MQTTPublisher
from .helper.mqtt_subscriber import MQTTSubscriber
from ..database.energy_database_controller import EnergyDatabaseController
from ..models.mqtt_config import MQTTConfig


class MQTTController(BaseMQTT):
  """
  Manages MQTT connections, subscriptions, and publishing for the OpenADR node.
  """

  def __init__(
    self,
    config: MQTTConfig,
    energy_database_controller: EnergyDatabaseController,
    ven_id: str = '',
  ) -> None:
    """
    Initialize the MQTTManager class.

    Parameters
    ----------
    config : MQTTConfig
        The MQTT configuration.
    energy_database_controller : EnergyDatabaseController
        The energy database controller.
    ven_id : str, optional
        The VEN ID, by default "".
    """
    if not config.is_valid():
      raise ValueError('Invalid MQTT configuration')

    super().__init__(
      config.broker,
      config.port,
      config.username,
      config.password,
      config.use_tls,
      config.ca_certs,
    )

    self.config = config
    self.energy_database_controller = energy_database_controller
    self._ven_id = ven_id

    # Initialize publisher and subscriber
    self.publisher = MQTTPublisher(self.client)
    self.subscriber = MQTTSubscriber(self.client)

    self.client.on_message = self._on_message

    self._stop_event = Event()

    # Additional setup
    self._setup_subscriptions()

  def signal_handler(self, signum, frame) -> None:
    """
    Handle system signals for graceful shutdown.

    Parameters
    ----------
    signum : int
        The signal number.
    frame : frame
        The current stack frame.
    """
    logger.info(f'Received signal {signum}. Initiating graceful shutdown...')
    self.stop()

  def _setup_subscriptions(self) -> None:
    """
    Set up topic subscriptions and their handlers.
    """
    if self.is_connected:
      try:
        for topic in self.config.topics:
          if topic.topic_type == 'sub':
            self.subscriber.subscribe_with_handler(
              topic.topic, self._handle_consumption_message
            )
      except Exception as e:
        logger.error(f'Failed to setup subscriptions: {e}', exc_info=True)

  def _handle_consumption_message(self, topic: str, payload: Any) -> None:
    """
    Handle consumption topic messages.

    Parameters
    ----------
    topic : str
        The topic of the message.
    payload : Any
        The payload of the message.
    """
    logger.debug('MQTT MESSAGE RECEIVED')
    try:
      data = json.loads(payload)
      data['ven_id'] = self._ven_id
      self.energy_database_controller.insert_consumption(data)
      logger.info(f'Processed consumption data from {topic}: {data}')
    except json.JSONDecodeError as e:
      logger.error(f'Failed to decode message payload: {e}')
    except Exception as e:
      logger.error(f'Failed to process message: {e}', exc_info=True)

  def _on_connect(self, client, userdata, flags, rc) -> None:
    """
    Override parent's _on_connect to add subscription.

    Parameters
    ----------
    client : mqtt.Client
        The MQTT client instance.
    userdata : Any
        User-defined data of any type.
    flags : Dict
        Response flags sent by the broker.
    rc : int
        The connection result.
    """
    super()._on_connect(client, userdata, flags, rc)
    if rc == 0:
      # Resubscribe to topics on reconnection
      self._setup_subscriptions()
    else:
      logger.error(f'Failed to connect with result code {rc}')

  def _on_message(self, client, userdata, msg) -> None:
    """
    Route incoming messages to appropriate handlers.

    Parameters
    ----------
    client : mqtt.Client
        The MQTT client instance.
    userdata : Any
        User-defined data of any type.
    msg : mqtt.MQTTMessage
        The MQTT message.
    """
    try:
      if not self._stop_event.is_set():  # Only process messages if not stopping
        payload = msg.payload.decode('utf-8')
        logger.debug(f'Received message on topic {msg.topic}: {payload}')
        self.subscriber.handle_message(msg.topic, payload)
    except Exception as e:
      logger.error(f'Error in message handling: {e}', exc_info=True)

  async def publish_load_profile(self) -> None:
    """
    Asynchronously publish load profile data.
    """
    while not self._stop_event.is_set():
      try:
        if not self.is_ready:
          logger.warning('Not ready for publishing. Waiting for connection...')
          await asyncio.sleep(5)
          continue

        load_profile = self.energy_database_controller.get_load_profile()
        if not load_profile['dstart'].size:
          await asyncio.sleep(10)
          continue

        current_time_ms = int(time.time() * 1000)
        nearest_idx = np.abs(load_profile['dstart'] - current_time_ms).argmin()
        nearest_row = {key: load_profile[key][nearest_idx] for key in load_profile}

        payload = float(nearest_row['signal_payload'])
        for topic in self.config.topics:
          if topic.topic_type == 'pub' and topic.topic == 'load_profile':
            self.publisher.publish(topic.topic, payload)
            logger.info(f'Published load profile to {topic.topic}: {payload}')

        await asyncio.sleep(30)

      except Exception as e:
        logger.error(f'Failed to publish load profile: {e}', exc_info=True)
        await asyncio.sleep(5)

  def start(self) -> None:
    """
    Start the MQTT client.
    """
    try:
      self._stop_event.clear()
      # Set last will and testament for clean disconnect notification
      self.client.will_set(f'status/{self._ven_id}', 'offline', qos=1, retain=True)
      self.client.loop_start()
      self.client.connect_async(
        self.config.broker, self.config.port, keepalive=self.config.keepalive
      )
      # Publish online status
      self.client.publish(f'status/{self._ven_id}', 'online', qos=1, retain=True)
      logger.info('MQTT client started and connecting...')
    except Exception as e:
      logger.error(f'Failed to start MQTT client: {e}', exc_info=True)
      self.stop()
      raise RuntimeError(f'MQTT client failed to start: {str(e)}')

  def stop(self) -> None:
    """
    Stop the MQTT client with guaranteed cleanup.
    """
    if not self._stop_event.is_set():
      try:
        logger.info('Initiating MQTT client shutdown...')
        self._stop_event.set()

        # Publish offline status before disconnecting
        if self.is_connected:
          self.client.publish(f'status/{self._ven_id}', 'offline', qos=1, retain=True)

        # Unsubscribe from all topics
        for topic in self.config.topics:
          if topic.topic_type == 'sub':
            self.client.unsubscribe(topic.topic)

        # Wait briefly for pending operations
        time.sleep(0.5)

        # Disconnect and stop the loop
        if self.client:
          self.client.disconnect()
          self.client.loop_stop()

        logger.info('MQTT client stopped successfully')
      except Exception as e:
        logger.error(f'Error during MQTT client shutdown: {e}', exc_info=True)
        raise RuntimeError(f'Failed to stop MQTT client: {str(e)}')
      finally:
        # Ensure the stop event is set even if an error occurred
        self._stop_event.set()
