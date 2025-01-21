# protocols/mqtt/handlers/consumption_handler.py
from typing import Any, Dict

from src.openadr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.openadr_node.protocols.mqtt.interfaces.mqtt_interface import IMessageHandler


class ConsumptionMessageHandler(IMessageHandler):
  def __init__(self, consumption_service: IConsumptionService):
    self._consumption_service = consumption_service

  async def handle_message(self, topic: str, payload: Dict[str, Any]) -> None:
    await self._consumption_service.process_consumption(payload)
