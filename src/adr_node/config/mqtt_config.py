from dataclasses import dataclass
from typing import List

from src.adr_node.config.topic_config import TopicConfig


@dataclass
class MQTTConfig:
  """
  Configuration settings for MQTT connection.

  Attributes
  ----------
  broker : str
      The MQTT broker address.
  port : int
      The port number for the MQTT broker.
  topics : List[TopicConfig]
      The list of MQTT topics.
  username : str
      The username for MQTT authentication.
  password : str
      The password for MQTT authentication.
  """

  broker: str
  port: int
  topics: List[TopicConfig]
  username: str
  password: str

  def is_valid(self) -> bool:
    """
    Check if all required MQTT configuration parameters are present.

    Returns
    -------
    bool
        True if all required parameters are present, False otherwise.
    """
    return all(
      [
        self.broker,
        self.port,
        self.username,
        self.password,
      ]
    )
