import asyncio
import json
import time
from threading import Event
from typing import Any

import numpy as np

from src.openadr_node import logger
from src.openadr_node.database import EnergyDatabaseController
from src.openadr_node.models.mqtt_config import MQTTConfig
from src.openadr_node.protocols.helper.base_mqtt import BaseMQTT
from src.openadr_node.protocols.helper.mqtt_publisher import MQTTPublisher
from src.openadr_node.protocols.helper.mqtt_subscriber import MQTTSubscriber
from src.openadr_node.protocols.mqtt.interfaces.mqtt_interface import IMQTTController
from src.openadr_node.protocols.mqtt.message_processors.consumption_message import (
  ConsumptionMessageProcessor,
)


class MQTTController(BaseMQTT, IMQTTController):
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
    Initialize the MQTTController class.

    Parameters
    ----------
    config : MQTTConfig
        The MQTT configuration containing broker details, credentials, and topics.
    energy_database_controller : EnergyDatabaseController
        The energy database controller responsible for database operations.
    ven_id : str, optional
        The VEN ID, by default "".
    """
    # Validate the configuration
    if not config.is_valid():
      raise ValueError('Invalid MQTT configuration')

    super().__init__(
      broker=config.broker,
      port=config.port,
      username=config.username,
      password=config.password,
      use_tls=config.use_tls,
      ca_certs=config.ca_certs,
    )

    self.config = config
    self.energy_database_controller = energy_database_controller
    self._ven_id = ven_id

    # Publisher/Subscriber setup
    self.publisher = MQTTPublisher(self.client)
    self.subscriber = MQTTSubscriber(self.client)

    # Custom message processor for consumption data
    self.consumption_processor = ConsumptionMessageProcessor(self._ven_id)

    # PyPI's paho-mqtt callback
    self.client.on_message = self._on_message

    # Event to coordinate stopping
    self._stop_event = Event()

    # Subscribe to topics if connected
    self._setup_subscriptions()

  def signal_handler(self, signum, frame) -> None:
    """
    Handle system signals for graceful shutdown.
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
            # Each subscription can use different handlers if needed
            self.subscriber.subscribe_with_handler(
              topics=topic.topic, handlers=self._handle_consumption_message
            )
      except Exception as e:
        logger.error(f'Failed to setup subscriptions: {e}', exc_info=True)

  def _handle_consumption_message(self, topic: str, payload: Any) -> None:
    """
    Handle consumption topic messages and delegate message processing.
    """
    logger.debug('Consumption message received on MQTT.')
    try:
      data = self.consumption_processor.parse_consumption_message(payload)
      self.energy_database_controller.insert_consumption(data)
      logger.info(f'Processed consumption data from {topic}: {data}')
    except json.JSONDecodeError as e:
      logger.error(f'Failed to decode message payload: {e}')
    except Exception as e:
      logger.error(f'Failed to process message: {e}', exc_info=True)

  def _on_connect(self, client, userdata, flags, rc) -> None:
    """
    Override parent's _on_connect to re-subscribe when connected.
    """
    super()._on_connect(client, userdata, flags, rc)
    if rc == 0:
      # Re-subscribe after reconnect
      self._setup_subscriptions()
    else:
      logger.error(f'Failed to connect with result code {rc}')

  def _on_message(self, client, userdata, msg) -> None:
    """
    Route incoming messages to the MQTTSubscriber for handling.
    """
    if not self._stop_event.is_set():
      try:
        payload_str = msg.payload.decode('utf-8')
        logger.debug(f'Received message on topic {msg.topic}: {payload_str}')
        # Subscriber routes the message to the correct handler
        self.subscriber.handle_message(msg.topic, payload_str)
      except Exception as e:
        logger.error(f'Error in message handling: {e}', exc_info=True)

  async def publish_load_profile(self) -> None:
    """
    Asynchronously publish load profile data in small intervals with exponential backoff.
    """
    max_attempts = 5
    attempt = 0
    backoff = 1

    while not self._stop_event.is_set():
      try:
        if not self.is_ready:
          logger.warning('Not ready for publishing. Waiting...')
          await asyncio.sleep(5)
          continue

        # Example log for demonstration
        logger.debug('About to publish load profile data.')
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
            self.publisher.publish(topic=topic.topic, payload=payload)
            logger.info(f'Published load profile to {topic.topic}: {payload}')

        # Reset attempt counter and backoff after successful publish
        attempt = 0
        backoff = 1

        # Adjust the sleep interval as needed
        await asyncio.sleep(30)

      except Exception as e:
        logger.error(f'Failed to publish load profile: {e}', exc_info=True)
        attempt += 1
        if attempt >= max_attempts:
          logger.error('Max attempts reached. Cancelling publish_load_profile.')
          break
        await asyncio.sleep(backoff)
        backoff *= 2  # Exponential backoff

  def start(self) -> None:
    """
    Start the MQTT client loop and connect asynchronously to the broker.
    """
    try:
      self._stop_event.clear()
      # Set Last Will & Testament
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
    Stop the MQTT client with proper cleanup.
    """
    if not self._stop_event.is_set():
      try:
        logger.info('Initiating MQTT client shutdown...')
        self._stop_event.set()

        # Publish offline before disconnect
        if self.is_connected:
          self.client.publish(f'status/{self._ven_id}', 'offline', qos=1, retain=True)

        # Unsubscribe from topics
        for topic in self.config.topics:
          if topic.topic_type == 'sub':
            self.client.unsubscribe(topic.topic)

        time.sleep(0.5)  # Wait briefly for queued operations

        # Disconnect and stop the loop
        if self.client:
          self.client.disconnect()
          self.client.loop_stop()
        logger.info('MQTT client stopped successfully')

      except Exception as e:
        logger.error(f'Error during MQTT client shutdown: {e}', exc_info=True)
        raise RuntimeError(f'Failed to stop MQTT client: {str(e)}')
      finally:
        self._stop_event.set()
