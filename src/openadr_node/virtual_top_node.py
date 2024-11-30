import asyncio
import logging
from functools import partial
from openleadr import OpenADRServer
from openleadr.utils import generate_id

from pydispatch import dispatcher

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VirtualTopNode:
  def __init__(self, server_name: str):
    self._server_name = server_name

    self._open_adr_server = OpenADRServer(self._server_name)
    self._init_default_handler()

    #dispatcher.connect(self._on_update_load_profile, signal='on_update_report') TODO: Replace signal

  def _init_default_handler(self):
    self._open_adr_server.add_handler(
      'on_create_party_registration', self._on_create_party_registration
    )
    self._open_adr_server.add_handler('on_register_report', self._on_register_report)

  async def _on_create_party_registration(self, registration_info: dict):
    ven_name = registration_info.get('ven_name')
    # TODO: Check in the database if VEN exists
    ven_id = "ven_123" # generate_id('ven_id')
    registration_id = generate_id()
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

    # Set the sampling interval for the report
    sampling_interval = min_sampling_interval
    logger.info(
      f'Report registered for VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )

    return callback, sampling_interval

  def _on_update_report(
    self, data: list, ven_id: str, resource_id: str, measurement: str
  ):
    # Handle incoming data for the report (customize as needed)
    logger.info(
      f'Report update received: VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )
    # Example: Processing the data here
    if data:
      logger.debug(f'Data: {data}')

    #dispatcher.send(signal='on_update_report', data=data)

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

  def _on_update_load_profile(self):
    print('Load profile has been updated')

  def get_open_adr_server_run(self):
    return self._open_adr_server.run()

  def dispatch_adr_event(self, event):
    print("NEXT STEP DISPATCH")
    print(event)
    if event:
      self._open_adr_server.add_event(
        ven_id=event.ven_id,
        signal_name=event.signal_name,
        signal_type=event.signal_type,
        intervals=event.intervals,
        callback=self.event_response_callback # self._event_callback,
      )

  async def event_response_callback(self, ven_id, event_id, opt_type):
    """
    Callback that receives the response from a VEN to an Event.
    """
    print(f"VEN {ven_id} responded to Event {event_id} with: {opt_type}")
