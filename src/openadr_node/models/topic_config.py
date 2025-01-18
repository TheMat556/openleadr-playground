from dataclasses import dataclass


@dataclass
class TopicConfig:
  """Configuration for MQTT topics.

  Args:
      topic: The topic name
      type: The type of the topic ('sub' or 'pub')
  """

  topic: str
  type: str
