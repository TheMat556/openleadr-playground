from dataclasses import dataclass
from typing import Optional, List
from .topic_config import TopicConfig


@dataclass
class MQTTConfig:
  """Configuration for MQTT client connection.

  Args:
      broker: MQTT broker address
      port: MQTT broker port
      username: Authentication username
      password: Authentication password
      use_tls: Whether to use TLS encryption
      ca_certs: Path to CA certificates for TLS
      client_id: Optional client identifier
      keepalive: Connection keepalive timeout in seconds
      topics: List of TopicConfig objects
  """

  broker: str
  port: int
  username: str
  password: str
  use_tls: bool = True
  ca_certs: Optional[str] = None
  client_id: Optional[str] = None
  keepalive: int = 60
  topics: List[TopicConfig] = None

  def is_valid(self) -> bool:
    """Check if the MQTT configuration is valid.

    Returns
    -------
    bool
        True if the configuration is valid, False otherwise.
    """
    if not self.broker:
      return False
    if not (1 <= self.port <= 65535):
      return False
    if not self.username:
      return False
    if not self.password:
      return False
    if not self.topics or not isinstance(self.topics, list):
      return False
    return True
