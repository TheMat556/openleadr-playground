import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Dict, Optional

from openleadr import OpenADRServer
from openleadr.utils import generate_id

from src.openadr_node import logger
from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.decorator.signal_connector import SignalConnector
from src.openadr_node.decorator.signal_sender import SignalSender


class VirtualTopNode(AdrBaseConfig):
  def __init__(self, server_name: str, path_prefix: Optional[str] = None):
    super().__init__()
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._registration_info: Dict[str, str] = {}
    self._server_name = server_name

    self._open_adr_server = OpenADRServer(
      self._server_name,
      http_host='0.0.0.0',
      http_path_prefix=path_prefix if path_prefix else '/OpenADR2/Simple/2.0b',
    )

    self._init_default_handler()

  def _init_default_handler(self):
    self._open_adr_server.add_handler(
      'on_create_party_registration', self._on_create_party_registration
    )
    self._open_adr_server.add_handler('on_register_report', self._on_register_report)

  async def _on_create_party_registration(self, registration_info: dict):
    ven_name = registration_info.get('ven_name')
    # TODO: Check in the database if VEN exists
    ven_id = generate_id('ven_id')
    registration_id = generate_id()
    self._registration_info[ven_id] = registration_id
    logger.info(
      f'Registered new VEN: {ven_name} with ID: {ven_id} and Registration ID: {registration_id}'
    )
    return ven_id, registration_id

  async def _on_register_report(
    self,
    ven_id: str,
    resource_id: str,
    measurement: str,
    unit: str,
    scale: str,
    min_sampling_interval: int,
    max_sampling_interval: int,
  ):
    callback = partial(
      self._on_update_report,
      ven_id=ven_id,
      resource_id=resource_id,
      measurement=measurement,
    )

    sampling_interval = min_sampling_interval
    logger.info(
      f'Report registered for VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )

    return callback, sampling_interval

  @SignalSender(signal='update_consumption_data', sender='vtn')
  def _on_update_report(
    self, data: list, ven_id: str, resource_id: str, measurement: str
  ):
    logger.info(
      f'Report update received: VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )

    # logic can be done in node manager, event could be general
    if measurement == 'energy':
      if ven_id not in self._ven_data:
        self._ven_data[ven_id] = {}

      self._ven_data[ven_id][resource_id] = data[0]
      # self._update_node_manager()

    if data:
      logger.debug(f'Data: {data}')

    return self._ven_data

  async def _event_callback(self, ven_id: str, event_id: str, opt_type: str):
    logger.info(f'The VEN {ven_id} decided to {opt_type} for Event ID: {event_id}')
    await self.handle_device_status(ven_id, opt_type)

  async def handle_device_status(self, ven_id: str, opt_type: str):
    # Simulating device interaction based on VEN's decision
    logger.info(
      f'Handling device status change for VEN ID: {ven_id}, Opt type: {opt_type}'
    )
    await asyncio.sleep(1)
    logger.info(f'Device status updated for VEN ID: {ven_id}, Opt type: {opt_type}')

  @SignalConnector('update_load_profile', 'nm')
  def _on_update_load_profile(self, signal, sender, data):
    print(data)
    print('LOADPROFILE has been updated')
    if data:
      for ven_id in self._ven_data.keys():
        self._open_adr_server.add_event(
          ven_id=ven_id,
          signal_type='level',
          signal_name='simple',
          intervals=[
            {
              'dtstart': datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
              'duration': timedelta(minutes=10),
              'signal_payload': 1,
            }
          ],
          callback=self._event_callback,
        )

  def get_open_adr_server_run(self):
    return self._open_adr_server.run()

  async def event_response_callback(self, ven_id, event_id, opt_type):
    """
    Callback that receives the response from a VEN to an Event.
    """
    print(f'VEN {ven_id} responded to Event {event_id} with: {opt_type}')
