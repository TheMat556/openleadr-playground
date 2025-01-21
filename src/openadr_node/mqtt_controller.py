import json
import ssl
import time
from threading import Event, Thread, Lock
from typing import Optional, Dict, Any, List

import numpy as np
import paho.mqtt.client as mqtt

from src.openadr_node import logger
from src.openadr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.openadr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.openadr_node.protocols.mqtt.config.mqtt_config import MQTTConfig


class MQTTManagerState:
  """Thread-safe state container for MQTT Manager."""

  def __init__(self):
    self._connected = False
    self._connection_rc = None
    self._lock: Lock = Lock()
    self._ready: Event = Event()

  @property
  def connected(self) -> bool:
    with self._lock:
      return self._connected

  @connected.setter
  def connected(self, value: bool) -> None:
    with self._lock:
      self._connected = value
      if value:
        self._ready.set()
      else:
        self._ready.clear()

  @property
  def connection_rc(self) -> Optional[int]:
    with self._lock:
      return self._connection_rc

  @connection_rc.setter
  def connection_rc(self, value: Optional[int]) -> None:
    with self._lock:
      self._connection_rc = value

  def wait_for_ready(self, timeout: Optional[float] = None) -> bool:
    """Wait for the connection to be ready."""
    return self._ready.wait(timeout=timeout)

  def is_ready(self) -> bool:
    """Check if the connection is ready."""
    return self._ready.is_set()


class MQTTManager:
  """
  Thread-safe MQTT communications manager for load profile and consumption data.

  This class safely handles MQTT connections, message publishing/subscribing, and automatic
  reconnection across multiple threads. Only one instance should be running at a time
  per broker connection.

  Args:
      config (MQTTConfig): Configuration object for MQTT client.

  Raises:
      ValueError: If the configuration is invalid.
      RuntimeError: If client is already running.
      ConnectionError: If broker connection fails.
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
    config: MQTTConfig,
    ven_name: str,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
  ) -> None:
    """Initialize MQTT Manager with thread-safe state."""
    if not config.is_valid():
      raise ValueError('Invalid MQTT configuration')

    self.config = config
    self.broker = config.broker
    self.port = config.port
    self.username = config.username
    self.password = config.password
    self.use_tls = config.use_tls
    self.ca_certs = config.ca_certs
    self.client_id = config.client_id or f'{config.username}_{int(time.time())}'
    self.keepalive = config.keepalive
    self.topics = config.topics or []

    # Thread-safe state
    self._state = MQTTManagerState()
    self._stop_event = Event()
    self._start_lock = Lock()
    self._threads: List[Thread] = []

    # Initialize MQTT client
    self.client = mqtt.Client(client_id=self.client_id, clean_session=True)
    self._configure_client()

  def _configure_client(self) -> None:
    """Configure MQTT client with provided settings."""
    try:
      if self.username and self.password:
        self.client.username_pw_set(self.username, self.password)

      if self.use_tls:
        self.client.tls_set(ca_certs=self.ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)
        self.client.tls_insecure_set(False)

      self.client.on_connect = self._on_connect
      self.client.on_disconnect = self._on_disconnect
      self.client.on_message = self._on_message

    except Exception as e:
      logger.error(f'Failed to configure MQTT client: {e}', exc_info=True)
      raise RuntimeError(f'MQTT client configuration failed: {str(e)}')

  def _on_connect(
    self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int
  ) -> None:
    """Handle connection callback from broker."""
    self._state.connection_rc = rc
    if rc == 0:
      self._state.connected = True
      logger.info(f'Connected successfully to {self.broker}')
      for topic in self.topics:
        self.client.subscribe(topic.name)
        logger.info(f'Subscribed to topic: {topic.name}')
    else:
      self._state.connected = False
      error_message = self.CONNECTION_RESPONSES.get(
        rc, f'Connection failed with code {rc}'
      )
      logger.error(error_message)

  def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
    """Handle disconnection events."""
    self._state.connected = False  # This will clear the ready event
    if rc != 0:
      logger.warning(f'Unexpected disconnection (RC: {rc}). Attempting reconnection...')
      try:
        self._reconnect()
      except ConnectionError as e:
        logger.error(f'Failed to reconnect: {e}')

  def _on_message(
    self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
  ) -> None:
    """Process incoming MQTT messages."""
    try:
      data = json.loads(msg.payload)
      # self.load_profile_manager.insert_consumption(data)
      logger.info(f'Processed consumption data: {data}')
    except json.JSONDecodeError as e:
      logger.error(f'Failed to decode message payload: {e}')
    except Exception as e:
      logger.error(f'Failed to process message: {e}', exc_info=True)

  def publish_load_profile(self) -> None:
    """Continuously publish load profile data while connected."""
    while not self._stop_event.is_set():
      try:
        # Check readiness instead of just connected state
        if not self._state.is_ready():
          logger.warning('Not ready for publishing. Waiting for connection...')
          if self._stop_event.wait(5):
            break
          continue

        # load_profile = self.load_profile_manager.get_load_profile()
        load_profile = {}
        if not load_profile['dstart'].size:
          if self._stop_event.wait(10):
            break
          continue

        # Convert timestamps safely
        current_time_ms = int(time.time() * 1000)
        nearest_idx = np.abs(load_profile['dstart'] - current_time_ms).argmin()
        nearest_row = {key: load_profile[key][nearest_idx] for key in load_profile}

        payload = float(nearest_row['signal_payload'])
        self.client.publish(self.topic_load_profile, payload)
        logger.info(f'Published load profile: {payload}')

      except Exception as e:
        logger.error(f'Failed to publish load profile: {e}', exc_info=True)

      if self._stop_event.wait(30):
        break

  def _reconnect(self, max_retries: int = 3, retry_delay: int = 5) -> bool:
    """
    Attempt to reconnect to the MQTT broker with proper state management.

    Args:
        max_retries (int): Maximum number of reconnection attempts.
        retry_delay (int): Delay between attempts in seconds.

    Returns:
        bool: True if reconnection successful.

    Raises:
        ConnectionError: If all reconnection attempts fail.
    """
    logger.info(f'Attempting to reconnect to broker {self.broker}...')

    for attempt in range(max_retries):
      logger.info(f'Reconnection attempt {attempt + 1}/{max_retries}')
      try:
        # First ensure we're properly disconnected
        try:
          self.client.disconnect()
        except Exception:
          pass  # Ignore errors during disconnect

        # Stop the network loop and reset client's internal state
        self.client.loop_stop()

        # Reconfigure client if needed
        if self.username and self.password:
          self.client.username_pw_set(self.username, self.password)

        if self.use_tls:
          self.client.tls_set(ca_certs=self.ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)
          self.client.tls_insecure_set(False)

        # Attempt to connect
        self.client.loop_start()
        result = self.client.connect(self.broker, self.port, keepalive=self.keepalive)

        if result == 0:  # 0 indicates success in MQTT
          # Wait for the on_connect callback to confirm connection
          if self._state.wait_for_ready(timeout=10):  # 10 second timeout
            logger.info('Successfully reconnected to broker')
            return True
          else:
            logger.error('Connection timeout waiting for broker response')
            self.client.loop_stop()
        else:
          logger.error(f'Connection failed with result code: {result}')
          self.client.loop_stop()

      except Exception as e:
        logger.error(f'Reconnection attempt failed: {str(e)}')
        # Ensure loop is stopped on error
        try:
          self.client.loop_stop()
        except Exception:
          pass

      # Wait before next attempt if we haven't succeeded
      if attempt < max_retries - 1:  # Don't sleep after the last attempt
        logger.info(f'Waiting {retry_delay} seconds before next attempt...')
        time.sleep(retry_delay)

    # If we get here, all attempts failed
    error_msg = 'All reconnection attempts failed'
    logger.error(error_msg)
    raise ConnectionError(error_msg)

  def start(self) -> None:
    """
    Start the MQTT client.

    Raises:
        RuntimeError: If client fails to start.
        ConnectionError: If broker connection fails or connection timeout occurs.
    """
    with self._start_lock:
      if self._state.connected:
        logger.warning('MQTT Manager already running')
        return

      try:
        # Reset state
        self._state.connected = False
        self._stop_event.clear()

        # Connect asynchronously
        self.client.loop_start()
        self.client.connect_async(self.broker, self.port, keepalive=60)
        logger.info('MQTT client started and connecting...')

      except Exception as e:
        logger.error(f'Failed to start MQTT client: {e}', exc_info=True)
        self.stop()  # Cleanup any partial startup
        raise RuntimeError(f'MQTT client failed to start: {str(e)}')

  def stop(self) -> None:
    """
    Gracefully stop the MQTT client.

    Thread-safe and idempotent - can be called multiple times safely.
    """
    with self._start_lock:
      try:
        self._stop_event.set()
        self.client.disconnect()
        self.client.loop_stop()
        self._state.connected = False
        logger.info('MQTT client stopped successfully')

      except Exception as e:
        logger.error(f'Error stopping MQTT client: {e}', exc_info=True)
        raise RuntimeError(f'Failed to stop MQTT client: {str(e)}')
