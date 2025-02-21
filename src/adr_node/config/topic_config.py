from dataclasses import dataclass
from enum import Enum


class TopicType(Enum):
  """
  Enumeration for topic types.

  Attributes
  ----------
  SUBSCRIBE : str
      Represents a subscription topic.
  PUBLISH : str
      Represents a publish topic.
  """

  SUBSCRIBE = 'sub'
  PUBLISH = 'pub'


@dataclass
class TopicConfig:
  """
  Configuration for MQTT topics.

  This class holds the configuration details for MQTT topics.

  Attributes
  ----------
  topic : str
      The topic name.
  topic_type : TopicType
      The type of the topic (TopicType.SUBSCRIBE or TopicType.PUBLISH).
  """

  topic: str
  topic_type: TopicType
