import asyncio
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Dict, List, Any, Tuple

from openleadr.utils import generate_id

from src.adr_node.core.nodes.configs.virtual_top_node_config import VirtualTopNodeConfig
from src.adr_node.core.nodes.interfaces.ivirtual_top_node import IVirtualTopNode
from src.adr_node.database.domain.data.consumption_data import ConsumptionData

from src.adr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.adr_node.database.domain.results.consumption_service_result import (
  ConsumptionServiceResult,
)
from src.adr_node.event_bus.constants.signal_types import SignalType
from src.adr_node.event_bus.decorators.emits_signal import emits_signal
from src.adr_node.event_bus.decorators.handle_signal import handle_signal
from src.adr_node.event_bus.decorators.init_signal_handlers import init_signal_handlers

from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus
from src.openadr_node import logger
from src.openadr_node.models.event import Interval


class VirtualTopNode(IVirtualTopNode):
  def __init__(
    self,
    config: VirtualTopNodeConfig,
    sqlite_consumption_service: IConsumptionService,
    event_bus: IEventBus,
  ):
    super().__init__()
    self._vtn_id = config.vtn_id
    self.http_host = config.http_host
    self.http_port = config.http_port
    self.path_prefix = config.path_prefix
    self.sqlite_consumption_service = sqlite_consumption_service
    self._open_adr_server = config.server_factory(
      vtn_id=config.vtn_id,
      http_host=config.http_host,
      http_port=config.http_port,
      http_path_prefix=config.path_prefix,
    )
    self.event_bus = event_bus
    self._registration_info: Dict[str, str] = {}
    self._init_default_handler()
    init_signal_handlers(self)

  def _init_default_handler(self) -> None:
    self._open_adr_server.add_handler(
      'on_create_party_registration', self._on_create_party_registration
    )
    self._open_adr_server.add_handler('on_register_report', self._on_register_report)

  async def _on_create_party_registration(
    self, registration_info: Dict[str, Any]
  ) -> Tuple[str, str]:
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
    self._send_register_report(ven_id)

    return callback, sampling_interval

  def _send_register_report(self, ven_id: str):
    return ven_id

  @emits_signal(SignalType.LOAD_PROFILE_UPDATED)
  def _on_update_report(
    self, data: List[Any], ven_id: str, resource_id: str, measurement: str
  ) -> None:
    logger.info(
      f'Report update received: VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )

    if measurement == 'energy':
      self.create_consumption_record(ven_id, resource_id, data[0])

  @handle_signal(SignalType.LOAD_PROFILE_UPDATED)
  def _tst(self, sender):  # Only accept sender parameter
    print(f'!!HANDLE_SIGNAL!! from {sender}')
    print('LOAD_PROFILE_UPDATED')

  def create_consumption_record(
    self, ven_id: str, resource_id: str, data: Tuple[datetime, float]
  ) -> ConsumptionServiceResult:
    timestamp, value = data
    consumption_data = ConsumptionData(
      timestamp=int(timestamp.timestamp()),
      ven_id=ven_id,
      resource_id=resource_id,
      value=value,
      created_at=int(datetime.now(timezone.utc).timestamp()),
      updated_at=None,
    )
    consumption_service_result = (
      self.sqlite_consumption_service.create_consumption_record(consumption_data)
    )
    return consumption_service_result

  async def _event_callback(self, ven_id: str, event_id: str, opt_type: str) -> None:
    logger.info(f'The VEN {ven_id} decided to {opt_type} for Event ID: {event_id}')
    await self.handle_device_status(ven_id, opt_type)

  async def handle_device_status(self, ven_id: str, opt_type: str) -> None:
    logger.info(
      f'Handling device status change for VEN ID: {ven_id}, Opt type: {opt_type}'
    )
    await asyncio.sleep(1)
    logger.info(f'Device status updated for VEN ID: {ven_id}, Opt type: {opt_type}')

  def _on_update_load_profile(
    self, signal: str, sender: str, data: Dict[str, List[Interval]]
  ) -> None:
    if data:
      for ven_id, intervals in data.items():
        if not isinstance(intervals, list):
          logger.error(
            f'Invalid intervals data for VEN {ven_id}: expected list, got {type(intervals)}'
          )
          continue

        # Check if the data is already formatted
        if not all(
          'dstart' in interval
          and 'duration' in interval
          and 'signal_payload' in interval
          for interval in intervals
        ):
          missing_fields = [
            field
            for field in ['dstart', 'duration', 'signal_payload']
            if not all(field in interval for interval in intervals)
          ]
          logger.error(
            f'Missing required fields for VEN {ven_id}: {", ".join(missing_fields)}'
          )
          intervals = (
            None  # NodeResourceController.process_load_profile_data(intervals)
          )

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
          and isinstance(interval['dstart'], (int, float))
          and isinstance(interval['duration'], (int, float))
          and interval['dstart'] > 0
          and interval['duration'] > 0
        ]
        if len(transformed_intervals) != len(intervals):
          logger.error(
            f'Failed to transform some intervals for VEN {ven_id} due to invalid timestamp data'
          )

        try:
          self._open_adr_server.add_event(
            ven_id=ven_id,
            signal_type='level',
            signal_name='simple',
            intervals=transformed_intervals,
            callback=self._event_callback,
          )
          if not transformed_intervals:
            logger.error(f'No valid intervals to process for VEN {ven_id}')
            return
          logger.info(
            f'[{datetime.now(timezone.utc).isoformat()}] Event added successfully for VEN: {ven_id} with {len(transformed_intervals)} intervals'
            f' from {transformed_intervals[0]["dtstart"]} to {transformed_intervals[-1]["dtstart"]}'
          )
        except ValueError as e:
          logger.error(f'Invalid data in event for VEN {ven_id}: {e}')
        except ConnectionError as e:
          logger.error(f'Failed to connect to OpenADR server for VEN {ven_id}: {e}')
        except Exception as e:
          logger.error(f'Failed to add event for VEN {ven_id}: {e}')
          logger.debug(
            f'Event processing failed for VEN {ven_id} with {len(transformed_intervals)} '
            f'intervals spanning {transformed_intervals[0]["dtstart"]} to '
            f'{transformed_intervals[-1]["dtstart"]}',
            exc_info=True,
          )

  def run(self):
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
