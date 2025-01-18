from dataclasses import dataclass
from enum import Enum


class TopicType(Enum):
  SUBSCRIBE = 'sub'
  PUBLISH = 'pub'


@dataclass
class TopicConfig:
  """Configuration for MQTT topics.

  Args:
      topic: The topic name
      topic_type: The type of the topic (TopicType.SUBSCRIBE or TopicType.PUBLISH)
  """

  topic: str
  topic_type: TopicType
