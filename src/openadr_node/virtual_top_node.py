import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Dict, Optional, List, Any, Tuple

from openleadr import OpenADRServer
from openleadr.utils import generate_id

from src.openadr_node import logger
from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.decorator.signal_connector import SignalConnector
from src.openadr_node.decorator.signal_sender import SignalSender
from src.openadr_node.models.event import ResourceConsumption


class VirtualTopNode(AdrBaseConfig):
  """
  Represents a Virtual Top Node (VTN) in the OpenADR system.
  """

  def __init__(
    self,
    server_name: str,
    http_port: Optional[int] = 8080,
    http_host: Optional[str] = '0.0.0.0',
    path_prefix: Optional[str] = None,
  ):
    """
    Initialize the VirtualTopNode.

    :param server_name: Name of the server.
    :type server_name: str
    :param http_port: HTTP port for the server.
    :type http_port: Optional[int]
    :param http_host: HTTP host for the server.
    :type http_host: Optional[str]
    :param path_prefix: Path prefix for the server.
    :type path_prefix: Optional[str]
    """
    super().__init__()
    self._ven_data: Dict[str, Dict[str, float]] = {}
    self._registration_info: Dict[str, str] = {}
    self._server_name = server_name
    self._open_adr_server = OpenADRServer(
      self._server_name,
      http_host=http_host,
      http_port=http_port,
      http_path_prefix=path_prefix if path_prefix else '/OpenADR2/Simple/2.0b',
    )

    self._init_default_handler()

  def _init_default_handler(self) -> None:
    """
    Initialize the default handlers for the OpenADR server.
    """
    self._open_adr_server.add_handler(
      'on_create_party_registration', self._on_create_party_registration
    )
    self._open_adr_server.add_handler('on_register_report', self._on_register_report)

  async def _on_create_party_registration(
    self, registration_info: Dict[str, Any]
  ) -> Tuple[str, str]:
    """
    Handle party registration.

    :param registration_info: Registration information.
    :type registration_info: Dict[str, Any]
    :return: Tuple containing VEN ID and registration ID.
    :rtype: Tuple[str, str]
    """
    ven_name = registration_info.get('ven_name')
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
  ) -> Tuple[partial, int]:
    """
    Handle report registration.

    :param ven_id: VEN ID.
    :type ven_id: str
    :param resource_id: Resource ID.
    :type resource_id: str
    :param measurement: Measurement type.
    :type measurement: str
    :param unit: Unit of measurement.
    :type unit: str
    :param scale: Scale of measurement.
    :type scale: str
    :param min_sampling_interval: Minimum sampling interval.
    :type min_sampling_interval: int
    :param max_sampling_interval: Maximum sampling interval.
    :type max_sampling_interval: int
    :return: Tuple containing the callback and sampling interval.
    :rtype: Tuple[partial, int]
    """
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

  def _on_update_report(
    self, data: List[Any], ven_id: str, resource_id: str, measurement: str
  ) -> Dict[str, Dict[str, float]]:
    """
    Handle report updates.

    :param data: Report data.
    :type data: List[Any]
    :param ven_id: VEN ID.
    :type ven_id: str
    :param resource_id: Resource ID.
    :type resource_id: str
    :param measurement: Measurement type.
    :type measurement: str
    :return: Updated VEN data.
    :rtype: Dict[str, Dict[str, float]]
    """
    logger.info(
      f'Report update received: VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )

    if measurement == 'energy':
      if ven_id not in self._ven_data:
        self._ven_data[ven_id] = {}

      self._ven_data[ven_id][resource_id] = data[0]
      self._send_consumption_data(ven_id, resource_id, data[0])

    if data:
      logger.debug(f'Data: {data}')

    return self._ven_data

  @SignalSender(signal='update_consumption_data', sender='vtn')
  def _send_consumption_data(
    self, ven_id: str, resource_id: str, data: float
  ) -> ResourceConsumption:
    """
    Send consumption data.

    :param ven_id: VEN ID.
    :type ven_id: str
    :param resource_id: Resource ID.
    :type resource_id: str
    :param data: Consumption data.
    :type data: float
    :return: Resource consumption object.
    :rtype: ResourceConsumption
    """
    resource_consumption = ResourceConsumption(
      ven_id=ven_id, resource_id=resource_id, data=data
    )
    return resource_consumption

  async def _event_callback(self, ven_id: str, event_id: str, opt_type: str) -> None:
    """
    Callback for event responses.

    :param ven_id: VEN ID.
    :type ven_id: str
    :param event_id: Event ID.
    :type event_id: str
    :param opt_type: Opt type.
    :type opt_type: str
    """
    logger.info(f'The VEN {ven_id} decided to {opt_type} for Event ID: {event_id}')
    await self.handle_device_status(ven_id, opt_type)

  async def handle_device_status(self, ven_id: str, opt_type: str) -> None:
    """
    Handle device status changes.

    :param ven_id: VEN ID.
    :type ven_id: str
    :param opt_type: Opt type.
    :type opt_type: str
    """
    logger.info(
      f'Handling device status change for VEN ID: {ven_id}, Opt type: {opt_type}'
    )
    await asyncio.sleep(1)
    logger.info(f'Device status updated for VEN ID: {ven_id}, Opt type: {opt_type}')

  @SignalConnector('update_load_profile', 'nm')
  def _on_update_load_profile(
    self, signal: str, sender: str, data: Dict[str, List[Dict[str, Any]]]
  ) -> None:
    """
    Update the load profile.

    :param signal: Signal name.
    :type signal: str
    :param sender: Signal sender.
    :type sender: str
    :param data: Load profile data with ven_id as keys and intervals as values.
    :type data: Dict[str, List[Dict[str, Any]]]
    """
    if data:
      for ven_id, intervals in data.items():
        if not isinstance(intervals, list):
          logger.error(f'Invalid intervals data for VEN {ven_id}: expected list')
          continue

        transformed_intervals = [
          {
            'dtstart': datetime.fromtimestamp(
              interval['dstart'] / 1000, tz=timezone.utc
            ),
            'duration': timedelta(milliseconds=interval['duration']),
            'signal_payload': interval['signal_payload'],
          }
          for interval in intervals
          if all(key in interval for key in ['dstart', 'duration', 'signal_payload'])
        ]

        try:
          self._open_adr_server.add_event(
            ven_id=ven_id,
            signal_type='level',
            signal_name='simple',
            intervals=transformed_intervals,
            callback=self._event_callback,
          )
          logger.info(f'Event added successfully for VEN: {ven_id}')
        except Exception as e:
          logger.error(f'Failed to add event for VEN {ven_id}: {e}')

  def get_open_adr_server_run(self) -> Any:
    """
    Get the OpenADR server run method.

    :return: The run method of the OpenADR server.
    :rtype: Any
    """
    return self._open_adr_server.run()

  async def event_response_callback(
    self, ven_id: str, event_id: str, opt_type: str
  ) -> None:
    """
    Callback that receives the response from a VEN to an Event.

    :param ven_id: VEN ID.
    :type ven_id: str
    :param event_id: Event ID.
    :type event_id: str
    :param opt_type: Opt type.
    :type opt_type: str
    """
    print(f'VEN {ven_id} responded to Event {event_id} with: {opt_type}')
