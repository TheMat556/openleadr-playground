import asyncio
import logging
from datetime import datetime, timedelta, timezone
from functools import partial
from typing import Dict, List, Any, Tuple

import numpy as np
from openleadr import enums
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
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.database.interfaces.services.iz_value_service import IZValueService
from src.adr_node.event_bus.constants.signal_types import SignalType
from src.adr_node.event_bus.decorators.handle_signal import handle_signal
from src.adr_node.event_bus.decorators.init_signal_handlers import init_signal_handlers

from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus


class VirtualTopNode(IVirtualTopNode):
  def __init__(
    self,
    config: VirtualTopNodeConfig,
    sqlite_consumption_service: IConsumptionService,
    load_profile_service: ILoadProfileService,
    z_value_service: IZValueService,
    event_bus: IEventBus,
  ):
    super().__init__()
    self._vtn_id = config.vtn_id
    self.http_host = config.http_host
    self.http_port = config.http_port
    self.path_prefix = config.path_prefix
    self.sqlite_consumption_service = sqlite_consumption_service
    self._load_profile_service = load_profile_service
    self._z_value_service = z_value_service
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
    logging.info(
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
    logging.info(
      f'Report registered for VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )
    self._send_register_report(ven_id)

    return callback, sampling_interval

  def _send_register_report(self, ven_id: str):
    return ven_id

  def _on_update_report(
    self, data: List[Any], ven_id: str, resource_id: str, measurement: str
  ) -> None:
    logging.info(
      f'Report update received: VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )

    if resource_id == 'base' and measurement == 'power':
      print('INRESOURCE', data)
      self.create_consumption_record(ven_id, resource_id, data[0])

  def create_consumption_record(
    self, ven_id: str, resource_id: str, data: Tuple[datetime, float]
  ) -> ConsumptionServiceResult | None:
    timestamp, value = data
    consumption_data = ConsumptionData(
      timestamp=int(timestamp.timestamp()),
      ven_id=ven_id,
      resource_id=resource_id,
      value=value,
      created_at=int(datetime.now(timezone.utc).timestamp()),
      updated_at=None,
      report_type=enums.REPORT_TYPE.USAGE,
      reading_type=enums.READING_TYPE.SUMMED,
    )
    consumption_service_result = (
      self.sqlite_consumption_service.create_consumption_record(consumption_data)
    )
    return consumption_service_result

  async def _event_callback(self, ven_id: str, event_id: str, opt_type: str) -> None:
    logging.info(f'The VEN {ven_id} decided to {opt_type} for Event ID: {event_id}')
    await self.handle_device_status(ven_id, opt_type)

  async def handle_device_status(self, ven_id: str, opt_type: str) -> None:
    logging.info(
      f'Handling device status change for VEN ID: {ven_id}, Opt type: {opt_type}'
    )
    await asyncio.sleep(1)
    logging.info(f'Device status updated for VEN ID: {ven_id}, Opt type: {opt_type}')

  @handle_signal(SignalType.LOAD_DISTRIBUTION_UPDATED)
  def _on_update_load_profile(self, sender: str) -> None:
    """
    Update the load profile in response to LOAD_DISTRIBUTION_UPDATED signal.
    Retrieves latest z-values and sends them to VENs.

    Args:
        sender: Signal sender identifier.
    """
    print(f'!!!Received LOAD_DISTRIBUTION_UPDATED signal from {sender}')
    try:
      # Get VENs active in the last hour
      vens_result = self.sqlite_consumption_service.get_vens_active_last_hour()
      if not vens_result.success or not vens_result.data.get('active_vens'):
        logging.warning('No active VENs found in the last hour.')
        return

      active_vens = vens_result.data['active_vens']
      logging.info(f'Active VENs in the last hour: {active_vens}')

      # Get latest z-values for active VENs
      z_values_result = self._z_value_service.get_latest_z_values()

      if not z_values_result.success:
        logging.error('Failed to get z-values')
        return

      # Create a mapping of VEN IDs to their z-values
      ven_z_values = {
        z_value.ven_id: z_value.z_value for z_value in z_values_result.data['z_values']
      }

      # Create a single interval for the current time
      current_time = datetime.now(timezone.utc)
      interval = {
        'dtstart': current_time,
        'duration': timedelta(minutes=15),  # or whatever duration you prefer
        'signal_payload': 0,  # will be replaced with z-value
      }

      # Schedule an event for each active VEN
      for ven_id in active_vens:
        z_value = ven_z_values.get(ven_id)
        if z_value is not None:
          interval_with_z = interval.copy()
          interval_with_z['signal_payload'] = z_value

          self._open_adr_server.add_event(
            ven_id=ven_id,
            signal_type='level',
            signal_name='simple',
            intervals=[interval_with_z],
            callback=self._event_callback,
          )
          logging.info(f'Event added for VEN {ven_id} with z-value: {z_value}')
        else:
          logging.warning(f'No z-value found for VEN {ven_id}')

    except Exception as e:
      logging.error(f'Failed to process load profile update: {e}')
      logging.debug('Load profile update failed', exc_info=True)

  def _convert_arrays_to_intervals(
    self,
    dtstart_array: np.ndarray,
    duration_array: np.ndarray,
    signal_payload_array: np.ndarray,
  ) -> List[Dict[str, Any]]:
    """
    Convert separate numpy arrays for each field into a list of intervals.

    Args:
        dtstart_array: Array of start timestamps
        duration_array: Array of durations
        signal_payload_array: Array of signal values

    Returns:
        List of intervals with dtstart, duration, and signal_payload.
    """
    intervals = []

    try:
      # Convert arrays to Python scalars and create intervals
      for i in range(len(dtstart_array)):
        interval = {
          'dtstart': int(dtstart_array[i].item() * 1000),  # Convert to milliseconds
          'duration': int(duration_array[i].item() * 1000),
          'signal_payload': float(signal_payload_array[i].item()),
        }
        intervals.append(interval)

    except (IndexError, ValueError, AttributeError) as e:
      logging.error(f'Error converting arrays to intervals: {e}')

    return intervals

  def _validate_interval(self, interval: Dict[str, Any]) -> bool:
    """
    Validate interval data.

    Args:
        interval: Interval data to validate.

    Returns:
        bool: True if interval is valid, False otherwise.
    """
    required_fields = ['dtstart', 'duration', 'signal_payload']

    if not all(field in interval for field in required_fields):
      return False

    try:
      return (
        isinstance(interval['dtstart'], (int, float))
        and isinstance(interval['duration'], (int, float))
        and interval['dtstart'] > 0
        and interval['duration'] > 0
      )
    except (TypeError, KeyError):
      return False

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
    logging.info(
      f'[event_response_callback] VEN={ven_id}, event_id={event_id}, opt_type={opt_type}'
    )
