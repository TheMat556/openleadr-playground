import time
from typing import Any
import logging

from hatch.cli.self import update
from openleadr import enums

from src.adr_node.communication.mqtt.config.mqtt_subscribe_service_config import \
  MQTTSubscribeServiceConfig
from src.adr_node.communication.mqtt.interfaces.imqtt_subscribe_service import (
  IMQTTSubscribeService,
)
from src.adr_node.communication.mqtt.services.mqtt_connection_service import (
  MQTTConnectionService,
)
from src.adr_node.database.domain.data.consumption_data import ConsumptionData
from src.adr_node.database.services.core.consumption_service import ConsumptionService
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus


class MQTTSubscribeService(IMQTTSubscribeService):
  """
  Handles MQTT subscription and message processing.

  Attributes
  ----------
  connection_handler : MQTTConnectionService
      The handler for the MQTT connection.
  consumption_service : ConsumptionService
      Service for handling consumption data.
  event_bus : IEventBus
      Event bus for handling events.

  Methods
  -------
  subscribe(topic: str) -> None
      Subscribes to a specific topic.
  handle_message(topic: str, payload: Any) -> None
      Handles incoming messages for a specific topic.
  """

  def __init__(
    self,
    config: MQTTSubscribeServiceConfig,
    connection_handler: MQTTConnectionService,
    consumption_service: ConsumptionService,
    event_bus: IEventBus,
  ):
    """
    Initializes the MQTTSubscribeHandler with the given parameters.

    Parameters
    ----------
    connection_handler : MQTTConnectionService
        The handler for the MQTT connection.
    consumption_service : ConsumptionService
        Service for handling consumption data.
    event_bus : IEventBus
        Event bus for handling events.
    """
    self.config = config
    self.connection_handler = connection_handler
    self.consumption_service = consumption_service
    self.event_bus = event_bus

  def subscribe(self, topic: str) -> None:
    """
    Subscribes to a specific topic.

    Parameters
    ----------
    topic : str
        The topic to subscribe to.
    """
    try:
      self.connection_handler.client.subscribe(topic)
      logging.info(f'Subscribed to topic: {topic}')
    except Exception as e:
      logging.error(f'Failed to subscribe to {topic}: {e}')

  def handle_message(self, topic: str, payload: Any) -> None:
    """
    Handles incoming messages for a specific topic.

    Parameters
    ----------
    topic : str
        The topic for which to handle incoming messages.
    payload : Any
        The message payload received.
    """
    try:
      if topic == 'consumption':
        consumption_data = ConsumptionData(
          timestamp=payload['timestamp'],
          ven_id=self.config.ven_id,
          resource_id='loxone',
          value=payload['value'],
          created_at=int(time.time()),
          updated_at=None,
          report_type=enums.REPORT_TYPE.USAGE,
          reading_type=enums.READING_TYPE.DIRECT_READ,
        )
        print("Consumption data received", consumption_data)

        result = self.consumption_service.create_consumption_record(consumption_data)
        print("Consumption data inserted", result)
        logging.info('Consumption data recorded successfully')
    except Exception as e:
      logging.error(f'Error processing message on topic {topic}: {e}')
