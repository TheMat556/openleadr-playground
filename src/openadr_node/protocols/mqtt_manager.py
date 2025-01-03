"""
MQTT Manager Module for handling MQTT communications.

This module provides a robust MQTT client implementation with automatic reconnection,
load profile publishing, and consumption data handling.
"""

import json
import logging
import ssl
import time
from threading import Event, Thread
from typing import Optional, Dict, Any

import paho.mqtt.client as mqtt

from src.openadr_node.database.loadprofile_manager import LoadProfileManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTManager:
  """
  Manages MQTT communications for load profile and consumption data.

  This class handles MQTT connections, message publishing/subscribing, and automatic
  reconnection in case of connection failures.

  Args:
      broker (str): MQTT broker address
      port (int): MQTT broker port
      topic_load_profile (str): Topic for publishing load profile data
      topic_consumption (str): Topic for receiving consumption data
      load_profile_manager (LoadProfileManager): Manager for handling load profiles
      username (str): MQTT authentication username
      password (str): MQTT authentication password
      use_tls (bool, optional): Enable TLS encryption. Defaults to True.
      ca_certs (Optional[str], optional): Path to CA certificates. Defaults to None.

  Attributes:
      connected (bool): Current connection status
      connection_rc (Optional[int]): Last connection return code
  """

  CONNECTION_RESPONSES = {
    0: 'Connected successfully',
    1: 'Connection refused - incorrect protocol version',
    2: 'Connection refused - invalid client identifier',
    3: 'Connection refused - server unavailable',
    4: 'Connection refused - bad username or password',
    5: 'Connection refused - not authorized',
  }

  def __init__(
    self,
    broker: str,
    port: int,
    topic_load_profile: str,
    topic_consumption: str,
    load_profile_manager: LoadProfileManager,
    username: str,
    password: str,
    use_tls: bool = True,
    ca_certs: Optional[str] = None,
  ) -> None:
    """Initialize the MQTT Manager with the given configuration."""
    self.broker = broker
    self.port = port
    self.topic_load_profile = topic_load_profile
    self.topic_consumption = topic_consumption
    self.load_profile_manager = load_profile_manager
    self.username = username
    self.password = password
    self.connected = False
    self.connection_rc = None
    self._stop_event = Event()

    # Create MQTT client with a unique ID
    client_id = f'{username}_{int(time.time())}'
    self.client = mqtt.Client(client_id=client_id, clean_session=True)

    self._configure_client(use_tls, ca_certs)

  def _configure_client(self, use_tls: bool, ca_certs: Optional[str]) -> None:
    """
    Configure MQTT client with authentication and TLS settings.

    Args:
        use_tls (bool): Whether to enable TLS
        ca_certs (Optional[str]): Path to CA certificates
    """
    try:
      if self.username and self.password:
        self.client.username_pw_set(self.username, self.password)

      if use_tls:
        self.client.tls_set(
          ca_certs=ca_certs,
          tls_version=ssl.PROTOCOL_TLS,
        )
        self.client.tls_insecure_set(False)

      self.client.on_connect = self._on_connect
      self.client.on_disconnect = self._on_disconnect
      self.client.on_message = self._on_message

    except Exception as e:
      logger.error(f'Failed to configure MQTT client: {e}', exc_info=True)
      raise

  def _on_connect(
    self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int
  ) -> None:
    """
    Handle connection callback from MQTT broker.

    Args:
        client: MQTT client instance
        userdata: User defined data
        flags: Response flags from broker
        rc: Return code
    """
    self.connection_rc = rc
    if rc == 0:
      self.connected = True
      logger.info(f'Connected successfully to {self.broker}')
      self.client.subscribe(self.topic_consumption)
    else:
      self.connected = False
      error_message = self.CONNECTION_RESPONSES.get(
        rc, f'Connection failed with code {rc}'
      )
      logger.error(error_message)

  def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
    """
    Handle disconnection events.

    Args:
        client: MQTT client instance
        userdata: User defined data
        rc: Return code
    """
    self.connected = False
    if rc != 0:
      logger.warning(f'Unexpected disconnection (RC: {rc}). Attempting reconnection...')
      self._reconnect()

  def _on_message(
    self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
  ) -> None:
    """
    Process incoming MQTT messages.

    Args:
        client: MQTT client instance
        userdata: User defined data
        msg: Received message
    """
    try:
      data = json.loads(msg.payload)
      self.load_profile_manager.insert_consumption(data)
      logger.debug(f'Processed consumption data: {data}')
    except json.JSONDecodeError as e:
      logger.error(f'Failed to decode message payload: {e}', exc_info=True)
    except Exception as e:
      logger.error(f'Failed to process message: {e}', exc_info=True)

  def _publish_load_profile(self) -> None:
    """Continuously publish load profile data while connected."""
    while not self._stop_event.is_set():
      try:
        if not self.connected:
          logger.warning('Not connected. Waiting for connection...')
          time.sleep(5)
          continue

        df = self.load_profile_manager.get_load_profile()
        if df.empty:
          continue

        current_time_ms = int(time.time() * 1000)
        nearest_idx = df.index[abs(df.index.astype(int) - current_time_ms).argmin()]
        nearest_row = df.loc[nearest_idx]

        payload = float(nearest_row['signal_payload'])
        self.client.publish(self.topic_load_profile, payload)
        logger.debug(f'Published load profile: {payload}')

      except Exception as e:
        logger.error(f'Failed to publish load profile: {e}', exc_info=True)

      time.sleep(5)

  def _reconnect(self, max_retries: int = 5, retry_delay: int = 5) -> bool:
    """
    Attempt to reconnect to the MQTT broker.

    Args:
        max_retries (int): Maximum number of reconnection attempts
        retry_delay (int): Delay between attempts in seconds

    Returns:
        bool: True if reconnection successful, False otherwise
    """
    for attempt in range(max_retries):
      try:
        logger.info(f'Attempting to reconnect... (Attempt {attempt + 1}/{max_retries})')
        self.client.connect(self.broker, self.port, keepalive=60)
        return True
      except Exception as e:
        logger.error(f'Reconnection attempt failed: {e}')
        time.sleep(retry_delay)
    return False

  def start(self) -> None:
    """
    Start the MQTT client and associated threads.

    Raises:
        Exception: If client fails to start
    """
    try:
      self.client.connect(self.broker, self.port, keepalive=60)
      Thread(
        target=self._publish_load_profile, name='PublishThread', daemon=True
      ).start()
      Thread(
        target=self.client.loop_forever, name='MQTTLoopThread', daemon=True
      ).start()
      logger.info('MQTT client started successfully')
    except Exception as e:
      logger.error(f'Failed to start MQTT client: {e}', exc_info=True)
      raise

  def stop(self) -> None:
    """Gracefully stop the MQTT client and all associated threads."""
    try:
      self._stop_event.set()
      self.client.disconnect()
      self.connected = False
      logger.info('MQTT client stopped successfully')
    except Exception as e:
      logger.error(f'Error stopping MQTT client: {e}', exc_info=True)
