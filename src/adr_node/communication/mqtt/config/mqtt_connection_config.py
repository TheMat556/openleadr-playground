from dataclasses import dataclass
from typing import Optional


@dataclass
class MQTTConnectionConfig:
  """
  Configuration for MQTT connection.

  Attributes
  ----------
  broker : str
      The address of the MQTT broker.
  port : int
      The port to connect to the MQTT broker.
  username : str
      The username for authentication with the MQTT broker.
  password : str
      The password for authentication with the MQTT broker.
  use_tls : bool, optional
      Whether to use TLS for the connection (default is False).
  ca_certs : Optional[str], optional
      Path to the CA certificate file for TLS (default is None).
  """

  broker: str
  port: int
  username: str
  password: str
  use_tls: bool = False
  ca_certs: Optional[str] = None
