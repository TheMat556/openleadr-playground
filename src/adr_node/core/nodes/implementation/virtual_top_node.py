import asyncio
import logging
import random
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
from src.adr_node.database.interfaces.services.ih_load_profile_service import (
  IHLoadProfileService,
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
  """
  Represents a Virtual Top Node (VTN) in the OpenADR system.

  Attributes
  ----------
  _vtn_id : str
      The ID of the Virtual Top Node.
  http_host : str
      The HTTP host for the VTN server.
  http_port : int
      The HTTP port for the VTN server.
  path_prefix : str
      The path prefix for the VTN server.
  sqlite_consumption_service : IConsumptionService
      Service for managing consumption data.
  _load_profile_service : ILoadProfileService
      Service for managing load profiles.
  _z_value_service : IZValueService
      Service for managing z-values.
  _open_adr_server : OpenADRServer
      The OpenADR server instance.
  event_bus : IEventBus
      The event bus for handling events.
  _registration_info : Dict[str, str]
      Dictionary to store registration information.
  """

  def __init__(
    self,
    config: VirtualTopNodeConfig,
    sqlite_consumption_service: IConsumptionService,
    load_profile_service: ILoadProfileService,
    z_value_service: IZValueService,
    h_load_profile_service: IHLoadProfileService,
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
    self._h_load_profile_service = h_load_profile_service
    self.event_bus = event_bus
    self._registration_info: Dict[str, str] = {}
    self._init_default_handler()
    init_signal_handlers(self)

  def _init_default_handler(self) -> None:
    """
    Initialize the default event handlers for the OpenADR server.
    """
    self._open_adr_server.add_handler(
      'on_create_party_registration', self._on_create_party_registration
    )
    self._open_adr_server.add_handler('on_register_report', self._on_register_report)

  async def _on_create_party_registration(
    self, registration_info: Dict[str, Any]
  ) -> Tuple[str, str]:
    """
    Handle the creation of a party registration.

    Args:
        registration_info (Dict[str, Any]): The registration information.

    Returns:
        Tuple[str, str]: The VEN ID and registration ID.
    """
    ven_name = registration_info.get('ven_name')
    # Generating a VEN ID with a prefix for clarity.
    ven_id = f'ven-{random.randint(1000, 9999)}'
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
    """
    Handle the registration of a report.

    Args:
        ven_id (str): The VEN ID.
        resource_id (str): The resource ID.
        measurement (str): The measurement type.
        unit (str): The unit of measurement.
        scale (str): The scale of measurement.
        min_sampling_interval (int): The minimum sampling interval.
        max_sampling_interval (int): The maximum sampling interval.

    Returns:
        Tuple[partial, int]: The callback and sampling interval.
    """
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
    return callback, sampling_interval

  def _on_update_report(
    self, data: List[Any], ven_id: str, resource_id: str, measurement: str
  ) -> None:
    """
    Handle the update of a report.

    Args:
        data (List[Any]): The report data.
        ven_id (str): The VEN ID.
        resource_id (str): The resource ID.
        measurement (str): The measurement type.
    """
    current_time = datetime.now(timezone.utc)
    logging.info(
      f'Report update received at {current_time.isoformat()}: '
      f'VEN ID: {ven_id}, Resource: {resource_id}, Measurement: {measurement}'
    )
    if resource_id == 'base' and measurement == 'power':
      self.create_consumption_record(ven_id, resource_id, data[0])
    if resource_id == 'h_load' and measurement == 'power':
      try:
        h_load_data = []
        for dt, value in data:
          h_load_data.append(
            {
              'timestamp': int(dt.timestamp()),
              'value': float(value),
              'ven_id': ven_id,
            }
          )
        h_load_data.sort(key=lambda x: x['timestamp'])
        result = self._h_load_profile_service.save_h_load_profile(
          data=h_load_data, ven_id=ven_id
        )
        if result.get('failed', 0) > 0:
          logging.error(
            f'Failed to save h-load profile data for VEN {ven_id} at {current_time.isoformat()}: {result["errors"]}'
          )
        else:
          logging.info(
            f'Successfully saved {result.get("success", 0)} h-load profile points for VEN {ven_id} at {current_time.isoformat()}'
          )
      except Exception as e:
        logging.error(
          f'Error processing h-load profile data for VEN {ven_id} at {current_time.isoformat()}: {str(e)}'
        )
        logging.debug('H-load profile processing failed', exc_info=True)

  def create_consumption_record(
    self, ven_id: str, resource_id: str, data: Tuple[datetime, float]
  ) -> ConsumptionServiceResult | None:
    """
    Create a consumption record.

    Args:
        ven_id (str): The VEN ID.
        resource_id (str): The resource ID.
        data (Tuple[datetime, float]): The consumption data.

    Returns:
        ConsumptionServiceResult | None: The result of the consumption service.
    """
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
    """
    Callback for handling event responses.

    Args:
        ven_id (str): The VEN ID.
        event_id (str): The event ID.
        opt_type (str): The opt type.
    """
    logging.info(f'The VEN {ven_id} decided to {opt_type} for Event ID: {event_id}')
    await self.handle_device_status(ven_id, opt_type)

  async def handle_device_status(self, ven_id: str, opt_type: str) -> None:
    """
    Handle the device status change.

    Args:
        ven_id (str): The VEN ID.
        opt_type (str): The opt type.
    """
    logging.info(
      f'Handling device status change for VEN ID: {ven_id}, Opt type: {opt_type}'
    )
    await asyncio.sleep(1)
    logging.info(f'Device status updated for VEN ID: {ven_id}, Opt type: {opt_type}')

  @handle_signal(SignalType.LOAD_DISTRIBUTION_UPDATED)
  def _on_update_load_profile(self, sender: str) -> None:
    """
    Update the load profile in response to the LOAD_DISTRIBUTION_UPDATED signal.
    Retrieves the latest z-values and creates intervals in the same format as the example:
      intervals = [
        {
          'dtstart': datetime.now(timezone.utc) + timedelta(minutes=1),
          'duration': timedelta(minutes=10),
          'signal_payload': 1,
        }
      ]
    Then sends one event per VEN using those intervals.

    Args:
        sender: Signal sender identifier.
    """
    try:
      z_values_result = self._z_value_service.get_latest_z_values()
      if not z_values_result.success:
        logging.error('Failed to get z-values for load profile update.')
        return

      events_by_ven: Dict[str, List[Dict[str, Any]]] = {}

      # Create intervals based on z-values from the service.
      # In this example, for each record we create an interval where dtstart is computed
      # as current time + a delay (for demonstration), duration is fixed, and payload is the z_value.
      for record in z_values_result.data['z_values']:
        if isinstance(record, dict):
          ven_id = record['ven_id']
          ts = record['timestamp']
          z_val = record['z_value']
        else:
          ven_id = record.ven_id
          ts = record.timestamp
          z_val = record.z_value

        # Skip invalid timestamps.
        if ts <= 0:
          continue

        # For demonstration, we use a fixed delay of 1 minute for dtstart.
        # dtstart = current_time + timedelta(minutes=1)
        dtstart = datetime.fromtimestamp(ts, tz=timezone.utc)
        interval = {
          'dtstart': dtstart,
          'duration': timedelta(minutes=15),
          'signal_payload': z_val,
        }
        events_by_ven.setdefault(ven_id, []).append(interval)

      # For each VEN, create one event containing the full profile (list of intervals).
      for ven_id, intervals in events_by_ven.items():
        if not intervals:
          logging.warning(
            f'No valid intervals for VEN {ven_id}; skipping event creation.'
          )
          continue
        # Optionally, sort intervals if needed.
        intervals.sort(key=lambda x: x['dtstart'])
        self._open_adr_server.add_event(
          ven_id=str(ven_id),
          signal_type='level',
          signal_name='simple',
          intervals=intervals,
          callback=self._event_callback,
        )
        logging.info(f'Event added for VEN {ven_id} with {len(intervals)} interval(s).')
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
        dtstart_array: Array of start timestamps.
        duration_array: Array of durations.
        signal_payload_array: Array of signal values.

    Returns:
        List of intervals with dtstart, duration, and signal_payload.
    """
    intervals = []
    try:
      for i in range(len(dtstart_array)):
        interval = {
          'dtstart': int(dtstart_array[i].item() * 1000),
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
    """
    Run the OpenADR server.

    Returns:
        The result of the server run method.
    """
    return self._open_adr_server.run()

  async def event_response_callback(
    self, ven_id: str, event_id: str, opt_type: str
  ) -> None:
    """
    Callback that receives the response from a VEN to an Event.

    Args:
        ven_id (str): The VEN ID.
        event_id (str): The event ID.
        opt_type (str): The opt type.
    """
    logging.info(
      f'[event_response_callback] VEN={ven_id}, event_id={event_id}, opt_type={opt_type}'
    )
    await self.handle_device_status(ven_id, opt_type)
