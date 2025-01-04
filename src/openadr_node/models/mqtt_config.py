from dataclasses import dataclass


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
  topic_load_profile : str
      The MQTT topic for load profile.
  topic_consumption : str
      The MQTT topic for consumption.
  username : str
      The username for MQTT authentication.
  password : str
      The password for MQTT authentication.
  """

  broker: str
  port: int
  topic_load_profile: str
  topic_consumption: str
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
        self.topic_load_profile,
        self.topic_consumption,
        self.username,
        self.password,
      ]
    )
