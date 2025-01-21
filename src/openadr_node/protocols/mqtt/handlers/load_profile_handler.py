# protocols/mqtt/handlers/load_profile_handler.py
from typing import Any, Dict

from src.openadr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.openadr_node.protocols.mqtt.interfaces.mqtt_interface import IMessageHandler


class LoadProfileMessageHandler(IMessageHandler):
  def __init__(self, load_profile_service: ILoadProfileService):
    self._load_profile_service = load_profile_service

  async def handle_message(self, topic: str, payload: Dict[str, Any]) -> None:
    await self._load_profile_service.process_load_profile(payload)
