import time
from datetime import timedelta

from src.adr_node.config.adr_config import AdrConfig
from src.adr_node.config.mqtt_config import MQTTConfig
from src.adr_node.config.report_config import ReportConfig
from src.adr_node.config.rest_api_config import RestApiConfig
from src.adr_node.config.topic_config import TopicConfig, TopicType
from src.adr_node.house_node.config.house_node_config import HouseNodeConfig
from src.adr_node.house_node.house_node import HouseNode


def temperature_callback() -> float:
  """Simulate temperature reading"""
  return 22.5


def energy_callback() -> float:
  """Simulate energy consumption reading"""
  return 1250.0


def main():
  adr_config = AdrConfig(
    node_id='house_001',
    ven_name='ven_001',
    vtn_url='http://localhost:8080/0/OpenADR2/Simple/2.0b',
  )

  mqtt_topics = [
    TopicConfig(topic='house/load_profile', topic_type=TopicType.PUBLISH),
    TopicConfig(topic='house/consumption', topic_type=TopicType.SUBSCRIBE),
  ]

  mqtt_config = MQTTConfig(
    broker='localhost',
    port=1883,
    username='mqtt_user',
    password='mqtt_pass',
    topics=mqtt_topics,
  )

  rest_config = RestApiConfig(
    port=8080,
  )

  house_node_config = HouseNodeConfig(
    adr_config=adr_config,
    mqtt_config=mqtt_config,
    rest_config=rest_config,
  )

  house = HouseNode(house_node_config)

  reports = [
    ReportConfig(
      resource_id='room_temp_001',
      measurement='temperature',
      sampling_rate=timedelta(seconds=60),
      callback=temperature_callback,
      additional_metadata={'unit': 'celsius', 'location': 'living_room'},
    ),
    ReportConfig(
      resource_id='energy_001',
      measurement='power',
      sampling_rate=timedelta(seconds=300),
      callback=energy_callback,
      additional_metadata={'unit': 'watts'},
    ),
  ]

  house.add_reports(reports)
  house.run()
  while True:
    time.sleep(1)


if __name__ == '__main__':
  main()
