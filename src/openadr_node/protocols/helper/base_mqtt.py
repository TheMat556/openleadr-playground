import ssl
import time
import uuid
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt
from paho.mqtt import MQTTException
from threading import Event, Lock
from src.openadr_node import logger


class BaseMQTT:
  """Base class for MQTT functionality."""

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
    username: str,
    password: str,
    use_tls: bool = True,
    ca_certs: Optional[str] = None,
  ) -> None:
    """
    Initialize the BaseMQTT class.

    Parameters
    ----------
    broker : str
        The MQTT broker address.
    port : int
        The port to connect to the MQTT broker.
    username : str
        The username for MQTT authentication.
    password : str
        The password for MQTT authentication.
    use_tls : bool, optional
        Whether to use TLS for the connection, by default True.
    ca_certs : Optional[str], optional
        Path to the CA certificate file, by default None.
    """
    self._validate_init_params(broker, port, username, password)

    self.broker = broker
    self.port = port
    self.username = username
    self.password = password

    # Thread-safe state
    self._connected = False
    self._connection_rc = None
    self._lock = Lock()
    self._ready = Event()

    # Initialize MQTT client
    client_id = f'{username}_{uuid.uuid4()}'
    self.client = mqtt.Client(client_id=client_id, clean_session=True)
    self._configure_client(use_tls, ca_certs)

  def _validate_init_params(
    self,
    broker: str,
    port: int,
    username: str,
    password: str,
  ) -> None:
    """
    Validate initialization parameters.

    Parameters
    ----------
    broker : str
        The MQTT broker address.
    port : int
        The port to connect to the MQTT broker.
    username : str
        The username for MQTT authentication.
    password : str
        The password for MQTT authentication.

    Raises
    ------
    ValueError
        If any of the string parameters are empty or if the port is not valid.
    """
    if not all([broker, username, password]):
      raise ValueError('All string parameters must be non-empty')
    if not isinstance(port, int) or port < 1 or port > 65535:
      raise ValueError('Port must be an integer between 1 and 65535')

  def _configure_client(self, use_tls: bool, ca_certs: Optional[str]) -> None:
    """
    Configure MQTT client with provided settings.

    Parameters
    ----------
    use_tls : bool
        Whether to use TLS for the connection.
    ca_certs : Optional[str]
        Path to the CA certificate file.

    Raises
    ------
    RuntimeError
        If the MQTT client configuration fails.
    """
    try:
      if self.username and self.password:
        self.client.username_pw_set(self.username, self.password)

      if use_tls:
        self.client.tls_set(ca_certs=ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2)
        self.client.tls_insecure_set(False)

      self.client.on_connect = self._on_connect
      self.client.on_disconnect = self._on_disconnect

    except (ssl.SSLError, MQTTException) as e:
      logger.error(f'Failed to configure MQTT client: {e}', exc_info=True)
      raise RuntimeError(f'MQTT client configuration failed: {str(e)}')

  def _on_connect(
    self, client: mqtt.Client, userdata: Any, flags: Dict, rc: int
  ) -> None:
    """
    Handle connection callback from broker.

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
    with self._lock:
      self._connection_rc = rc
      if rc == 0:
        self._connected = True
        self._ready.set()
        logger.info(f'Connected successfully to {self.broker}')
      else:
        self._connected = False
        self._ready.clear()
        error_message = self.CONNECTION_RESPONSES.get(
          rc, f'Connection failed with code {rc}'
        )
        logger.error(error_message)

  def _on_disconnect(self, client: mqtt.Client, userdata: Any, rc: int) -> None:
    """
    Handle disconnection events.

    Parameters
    ----------
    client : mqtt.Client
        The MQTT client instance.
    userdata : Any
        User-defined data of any type.
    rc : int
        The disconnection result.
    """
    with self._lock:
      self._connected = False
      self._ready.clear()
    if rc != 0:
      logger.warning(f'Unexpected disconnection (RC: {rc}). Attempting reconnection...')
      try:
        self._reconnect()
      except ConnectionError as e:
        logger.error(f'Failed to reconnect: {e}')

  def _reconnect(self, max_retries: int = 5, retry_delay: int = 5) -> bool:
    """
    Attempt to reconnect to the MQTT broker.

    Parameters
    ----------
    max_retries : int, optional
        Maximum number of reconnection attempts, by default 5.
    retry_delay : int, optional
        Delay between reconnection attempts in seconds, by default 5.

    Returns
    -------
    bool
        True if reconnection is successful, False otherwise.

    Raises
    ------
    ConnectionError
        If all reconnection attempts fail.
    """
    for attempt in range(max_retries):
      try:
        logger.info(f'Attempting to reconnect... (Attempt {attempt + 1}/{max_retries})')
        self.client.connect(self.broker, self.port, keepalive=60)
        return True
      except MQTTException as e:
        logger.error(f'Reconnection attempt failed: {e}')
        time.sleep(retry_delay)

    raise ConnectionError('All reconnection attempts failed')

  @property
  def is_connected(self) -> bool:
    """
    Thread-safe connection status check.

    Returns
    -------
    bool
        True if connected, False otherwise.
    """
    with self._lock:
      return self._connected

  @property
  def is_ready(self) -> bool:
    """
    Check if the connection is ready.

    Returns
    -------
    bool
        True if the connection is ready, False otherwise.
    """
    return self._ready.is_set()
