import json
import logging
import ssl
import time
from threading import Event, Thread, Lock
from typing import Optional, Dict, Any, List

import numpy as np
import paho.mqtt.client as mqtt

from src.openadr_node.database.loadprofile_manager import LoadProfileManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MQTTManagerState:
  """Thread-safe state container for MQTT Manager"""

  def __init__(self):
    self._connected = False
    self._connection_rc = None
    self._lock = Lock()
    self._ready = Event()  # New: Ready state for connection completion

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

  Thread Safety:
  - All shared state is protected by locks
  - Methods are reentrant and thread-safe
  - Start/Stop operations are atomic and idempotent

  Usage:
      manager = MQTTManager(...)
      try:
          manager.start()  # Start MQTT client and worker threads
          # ... application code ...
      finally:
          manager.stop()   # Cleanup resources

  Args:
      broker: MQTT broker address
      port: MQTT broker port
      topic_load_profile: Topic for publishing load profile data
      topic_consumption: Topic for receiving consumption data
      load_profile_manager: Manager for handling load profiles
      username: MQTT authentication username
      password: MQTT authentication password
      use_tls: Enable TLS encryption (default: True)
      ca_certs: Path to CA certificates (default: None)

  Raises:
      ValueError: If required parameters are invalid
      RuntimeError: If client is already running
      ConnectionError: If broker connection fails
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
    """Initialize MQTT Manager with thread-safe state."""
    self._validate_init_params(
      broker, port, topic_load_profile, topic_consumption, username, password
    )

    self.broker = broker
    self.port = port
    self.topic_load_profile = topic_load_profile
    self.topic_consumption = topic_consumption
    self.load_profile_manager = load_profile_manager
    self.username = username
    self.password = password

    # Thread-safe state
    self._state = MQTTManagerState()
    self._stop_event = Event()
    self._start_lock = Lock()
    self._threads: List[Thread] = []

    # Initialize MQTT client
    client_id = f'{username}_{int(time.time())}'
    self.client = mqtt.Client(client_id=client_id, clean_session=True)
    self._configure_client(use_tls, ca_certs)

  def _validate_init_params(
    self,
    broker: str,
    port: int,
    topic_load_profile: str,
    topic_consumption: str,
    username: str,
    password: str,
  ) -> None:
    """Validate initialization parameters."""
    if not all([broker, topic_load_profile, topic_consumption, username, password]):
      raise ValueError('All string parameters must be non-empty')
    if not isinstance(port, int) or port < 1 or port > 65535:
      raise ValueError('Port must be an integer between 1 and 65535')

  def _configure_client(self, use_tls: bool, ca_certs: Optional[str]) -> None:
    """Configure MQTT client with provided settings."""
    try:
      if self.username and self.password:
        self.client.username_pw_set(self.username, self.password)

      if use_tls:
        self.client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)
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
      self._state.connected = True  # This will also set the ready event
      logger.info(f'Connected successfully to {self.broker}')
      self.client.subscribe(self.topic_consumption)
    else:
      self._state.connected = False  # This will clear the ready event
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
      self.load_profile_manager.insert_consumption(data)
      logger.debug(f'Processed consumption data: {data}')
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
          print('STEP0.8')
          if self._stop_event.wait(5):
            break
          continue

        print('STEP0.9')
        load_profile = self.load_profile_manager.get_load_profile()
        print(load_profile)
        if not load_profile['dstart'].size:
          if self._stop_event.wait(10):
            break
          continue

        print('STEP1')
        # Convert timestamps safely
        current_time_ms = int(time.time() * 1000)
        nearest_idx = np.abs(load_profile['dstart'] - current_time_ms).argmin()
        nearest_row = {key: load_profile[key][nearest_idx] for key in load_profile}

        print('STEP2')
        payload = float(nearest_row['signal_payload'])
        print('Payload: ', payload)
        self.client.publish(self.topic_load_profile, payload)
        logger.info(f'Published load profile: {payload}')

      except Exception as e:
        logger.error(f'Failed to publish load profile: {e}', exc_info=True)

      if self._stop_event.wait(30):
        break

  def _reconnect(self, max_retries: int = 5, retry_delay: int = 5) -> bool:
    """
    Attempt to reconnect to the MQTT broker.

    Args:
        max_retries: Maximum number of reconnection attempts
        retry_delay: Delay between attempts in seconds

    Returns:
        bool: True if reconnection successful

    Raises:
        ConnectionError: If all reconnection attempts fail
    """
    for attempt in range(max_retries):
      try:
        logger.info(f'Attempting to reconnect... (Attempt {attempt + 1}/{max_retries})')
        self.client.connect(self.broker, self.port, keepalive=60)
        return True
      except Exception as e:
        logger.error(f'Reconnection attempt failed: {e}')
        time.sleep(retry_delay)

    raise ConnectionError('All reconnection attempts failed')

  def start(self) -> None:
    """
    Start the MQTT client.

    Raises:
        RuntimeError: If client fails to start
        ConnectionError: If broker connection fails or connection timeout occurs
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
        self._state.connected = False
        logger.info('MQTT client stopped successfully')

      except Exception as e:
        logger.error(f'Error stopping MQTT client: {e}', exc_info=True)
        raise RuntimeError(f'Failed to stop MQTT client: {str(e)}')
