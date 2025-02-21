import time

import paho.mqtt.client as mqtt
from typing import Any, Dict
import logging

from src.adr_node.communication.mqtt.config.mqtt_connection_config import (
  MQTTConnectionConfig,
)
from src.adr_node.communication.mqtt.interfaces.imqtt_connection_service import (
  IMQTTConnectionService,
)


class MQTTConnectionService(IMQTTConnectionService):
  """
  Handles the MQTT connection.

  Attributes
  ----------
  config : MQTTConnectionConfig
      Configuration for the MQTT connection.
  client : mqtt.Client
      The MQTT client instance.
  _connected : bool
      Connection status of the MQTT client.

  Methods
  -------
  configure_client(on_message_callback: Any = None) -> None
      Configures the MQTT client with the provided settings.
  connect() -> None
      Establishes a connection to the MQTT broker.
  publish(topic: str, payload: str) -> None
      Publishes a message to a specific topic.
  disconnect() -> None
      Disconnects from the MQTT broker.
  start_loop() -> None
      Starts the MQTT client loop.
  stop_loop() -> None
      Stops the MQTT client loop.
  is_connected() -> bool
      Checks if the client is currently connected to the MQTT broker.
  """

  def __init__(self, config: MQTTConnectionConfig):
    """
    Initializes the MQTTConnectionHandler with the given configuration.

    Parameters
    ----------
    config : MQTTConnectionConfig
        The configuration for the MQTT connection.
    """
    self.config = config
    client_id = f'tst_{int(time.time())}'  # Add timestamp for unique client ID
    self.client = mqtt.Client(client_id=client_id, clean_session=True)
    self._connected = False
    self.client.on_connect = self._on_connect
    self.client.on_disconnect = self._on_disconnect
    self._configure_client()

  def _configure_client(self) -> None:
    """Configure the MQTT client with all necessary settings."""
    logging.info('Configuring MQTT client.')

    if self.config.username and self.config.password:
      self.client.username_pw_set(self.config.username, self.config.password)

    self.client.tls_set()
    self.client.tls_insecure_set(True)

  def configure_client(self, on_message_callback: Any = None) -> None:
    """
    Configure message callback if needed.

    Parameters
    ----------
    on_message_callback : Any, optional
        The callback function for handling incoming messages (default is None).
    """
    if on_message_callback:
      self.client.on_message = on_message_callback

  def connect(self) -> None:
    """Establishes a connection to the MQTT broker."""
    try:
      logging.info(
        f'Connecting to broker {self.config.broker} on port {self.config.port}'
      )
      self.client.connect(self.config.broker, self.config.port, keepalive=60)
      self.client.loop_start()
    except Exception as e:
      logging.error(f'Failed to connect to broker: {e}')
      raise

  def publish(self, topic: str, payload: str) -> None:
    """
    Publishes a message to a specific topic.

    Parameters
    ----------
    topic : str
        The topic to publish the message to.
    payload : str
        The message payload to publish.
    """
    if self._connected:
      self.client.publish(topic, payload)
      logging.info(f'Published message to {topic}')
    else:
      logging.error('Cannot publish - not connected')

  def disconnect(self) -> None:
    """Disconnects from the MQTT broker."""
    self.client.disconnect()
    self.client.loop_stop()
    self._connected = False
    logging.info('MQTT client disconnected and loop stopped.')

  def start_loop(self) -> None:
    """Starts the MQTT client loop."""
    self.client.loop_start()
    logging.info('MQTT client loop started.')

  def stop_loop(self) -> None:
    """Stops the MQTT client loop."""
    self.client.loop_stop()
    logging.info('MQTT client loop stopped.')

  def is_connected(self) -> bool:
    """
    Checks if the client is currently connected to the MQTT broker.

    Returns
    -------
    bool
        True if the client is connected, False otherwise.
    """
    return self._connected

  def _on_connect(self, client: Any, userdata: Any, flags: Dict, rc: int) -> None:
    """
    Callback for when the client receives a CONNACK response from the server.

    Parameters
    ----------
    client : Any
        The client instance for this callback.
    userdata : Any
        The private user data as set in Client() or userdata_set().
    flags : Dict
        Response flags sent by the broker.
    rc : int
        The connection result.
    """
    if rc == 0:
      self._connected = True
      logging.info(f'Connected successfully to {self.config.broker}')
    else:
      self._connected = False
      logging.error(f'Connection to {self.config.broker} failed with code {rc}')

  def _on_disconnect(self, client: Any, userdata: Any, rc: int) -> None:
    """
    Callback for when the client disconnects from the broker.

    Parameters
    ----------
    client : Any
        The client instance for this callback.
    userdata : Any
        The private user data as set in Client() or userdata_set().
    rc : int
        The disconnection result.
    """
    self._connected = False
    if rc != 0:
      logging.warning('Unexpected disconnection from MQTT broker')
