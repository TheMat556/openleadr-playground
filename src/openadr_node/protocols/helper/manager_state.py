from threading import Event, Lock
from typing import Optional


class MQTTState:
  """Thread-safe state container for MQTT connections."""

  def __init__(self) -> None:
    """
    Initialize the MQTTState class.
    """
    self._connected = False
    self._connection_rc = None
    self._lock: Lock = Lock()
    self._ready: Event = Event()

  @property
  def connected(self) -> bool:
    """
    Get the connection status.

    Returns
    -------
    bool
        True if connected, False otherwise.
    """
    with self._lock:
      return self._connected

  @connected.setter
  def connected(self, value: bool) -> None:
    """
    Set the connection status.

    Parameters
    ----------
    value : bool
        The new connection status.
    """
    with self._lock:
      self._connected = value
      if value:
        self._ready.set()
      else:
        self._ready.clear()

  @property
  def connection_rc(self) -> Optional[int]:
    """
    The connection return code, or None if not set. Possible values:
    0: Connection successful
    1: Connection refused - incorrect protocol version
    2: Connection refused - invalid client identifier
    3: Connection refused - server unavailable
    4: Connection refused - bad username or password
    5: Connection refused - not authorized

    Returns
    -------
    Optional[int]
        The connection return code, or None if not set.
    """
    with self._lock:
      return self._connection_rc

  @connection_rc.setter
  def connection_rc(self, value: Optional[int]) -> None:
    """
    Set the connection return code.

    Parameters
    ----------
    value : Optional[int]
        The new connection return code.
    """
    with self._lock:
      self._connection_rc = value

  def wait_for_ready(self, timeout: Optional[float] = None) -> bool:
    """
    Wait for the connection to be ready.

    Parameters
    ----------
    timeout : Optional[float], optional
        The maximum time to wait in seconds, by default None.

    Returns
    -------
    bool
        True if the connection is ready within the timeout, False otherwise.
    """
    return self._ready.wait(timeout=timeout)

  def is_ready(self) -> bool:
    """
    Check if the connection is ready.

    Returns
    -------
    bool
        True if the connection is ready, False otherwise.
    """
    return self._ready.is_set()
