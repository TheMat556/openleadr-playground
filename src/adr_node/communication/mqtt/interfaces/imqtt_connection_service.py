from abc import ABC, abstractmethod


class IMQTTConnectionService(ABC):
  """
  Abstract base class for MQTT connection handlers.

  Methods
  -------
  configure_client(username: str, password: str) -> None
      Configures the MQTT client with the provided username and password.
  connect() -> None
      Establishes a connection to the MQTT broker.
  disconnect() -> None
      Disconnects from the MQTT broker.
  is_connected() -> bool
      Checks if the client is currently connected to the MQTT broker.
  """

  @abstractmethod
  def configure_client(self, username: str, password: str) -> None:
    """
    Configures the MQTT client with the provided username and password.

    Parameters
    ----------
    username : str
        The username for authentication with the MQTT broker.
    password : str
        The password for authentication with the MQTT broker.
    """
    pass

  @abstractmethod
  def connect(self) -> None:
    """
    Establishes a connection to the MQTT broker.
    """
    pass

  @abstractmethod
  def disconnect(self) -> None:
    """
    Disconnects from the MQTT broker.
    """
    pass

  @abstractmethod
  def is_connected(self) -> bool:
    """
    Checks if the client is currently connected to the MQTT broker.

    Returns
    -------
    bool
        True if the client is connected, False otherwise.
    """
    pass
