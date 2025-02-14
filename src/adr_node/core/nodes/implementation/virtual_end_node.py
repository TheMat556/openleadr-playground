import logging
from datetime import timezone, datetime, timedelta
from functools import wraps
from typing import Any, List, Optional, Dict, Callable

from openleadr import enums

from src.adr_node.config.report_config import ReportConfig
from src.adr_node.core.nodes.configs.virtual_end_node_config import VirtualEndNodeConfig
from src.adr_node.core.nodes.interfaces.ivirtual_end_node import IVirtualEndNode
from src.adr_node.database.domain.data.consumption_data import ConsumptionData
from src.adr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus

BASE_RESOURCE_ID = 'base'


class VirtualEndNode(IVirtualEndNode):
  def __init__(
    self,
    config: VirtualEndNodeConfig,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
    event_bus: IEventBus,
  ):
    super().__init__()
    self._ven_name = config.ven_name
    self._vtn_url = config.vtn_url
    self._open_adr_client = config.client_factory(self._ven_name, self._vtn_url)
    self._event_bus = event_bus
    self._load_profile_service = load_profile_service
    self._consumption_service = consumption_service
    self._init_default_handler()
    self._base_event_registered = False
    self._base_consumption = 0.0

  def run(self):
    return self._open_adr_client.run()

  def _init_default_handler(self) -> None:
    """
    Initialize the default event handler for the OpenADR client.
    """
    self._open_adr_client.add_handler('on_event', self.tst)

  async def tst(self, event):
    print('GOT EVENT', event)
    logging.info(f'[{datetime.now(timezone.utc).isoformat()}] Processing OpenADR event')
    required_keys = {
      'event_descriptor',
      'active_period',
      'event_signals',
      'targets',
    }
    if not all(key in event for key in required_keys):
      raise KeyError(f'Event missing required fields: {required_keys}')

    _event_descriptor = event['event_descriptor']
    _active_period = event['active_period']
    _event_signals = event['event_signals']
    _targets = event['targets']

    if not isinstance(_event_signals, list) or not all(
      isinstance(signal, dict) for signal in _event_signals
    ):
      raise ValueError('Invalid event_signals format')

    current_time = datetime.now(timezone.utc)
    flattened_intervals = [
      {
        'dtstart': int(current_time.timestamp()),
        'duration': int(interval['duration'].total_seconds()),
        'signal_payload': interval['signal_payload'],
      }
      for signal in _event_signals
      for interval in signal.get('intervals', [])
      if 'dtstart' in interval
      and 'duration' in interval
      and 'signal_payload' in interval
    ]

    if not flattened_intervals:
      raise ValueError('No valid intervals found in event_signals')

    logging.info(
      f'Created intervals with current time {current_time.strftime("%Y-%m-%d %H:%M:%S")}'
    )
    for interval in flattened_intervals:
      logging.info(
        f'Interval - Start: {interval["dtstart"]}, '
        f'Duration: {interval["duration"]}, '
        f'Payload: {interval["signal_payload"]}'
      )

    self._load_profile_service.save_load_profile(flattened_intervals)
    return 'optIn'

  def _wrap_callback(
    self, callback: Callable[..., float], report_config: ReportConfig
  ) -> Callable[..., float]:
    @wraps(callback)
    def wrapper(*args, **kwargs):
      print('!!!!wrapper!!!!', report_config.resource_id)
      if callable(callback):
        timestamp = datetime.now(timezone.utc)
        result = callback(*args, **kwargs)

        if result is None:
          logging.warning(
            f'Callback for report {report_config.resource_id} returned None'
          )
          return 0.0

        if not isinstance(result, (int, float)):
          logging.error(
            f'Callback for report {report_config.resource_id} returned non-numeric value: {result}'
          )
          return 0.0

        current_timestamp = int(timestamp.timestamp())

        report_type = (
          str(report_config.report_type)
          if report_config.report_type
          else str(enums.REPORT_TYPE.USAGE)
        )
        reading_type = (
          str(report_config.reading_type)
          if report_config.reading_type
          else str(enums.READING_TYPE.DIRECT_READ)
        )

        consumption_record = ConsumptionData(
          timestamp=current_timestamp,
          ven_id=self._ven_name,
          resource_id=report_config.resource_id,
          value=float(result),
          created_at=current_timestamp,
          report_type=report_type,
          reading_type=reading_type,
          updated_at=current_timestamp,
        )

        # Remove the base resource check to allow base reports to be recorded
        if report_config.resource_id != BASE_RESOURCE_ID:
          service_result = self._consumption_service.create_consumption_record(
            consumption_record
          )

          if not service_result.success:
            logging.error(
              f'Failed to create consumption record: {service_result.error}'
            )

        return result

      return 0.0

    print(wrapper)
    return wrapper

  def _get_current_consumption(self) -> float:
    """
    Get the current consumption data.

    Returns:
        float: The total current consumption value in kWh. Returns 0.0 if no data is available.
    """
    consumption_result = self._consumption_service.get_current_consumption()
    print('!!!!get_current_consumption!!!!', consumption_result)

    if consumption_result.success:
      # Get total consumption from the updated response structure
      total_consumption = consumption_result.data.get('total_consumption', 0.0)

      # Log detailed consumption information
      logging.info(f'Total consumption: {total_consumption} kWh')

      # Log additional metrics
      logging.info(
        f'Average consumption: {consumption_result.data.get("average_consumption", 0.0):.2f} kWh'
      )
      logging.info(f'Number of points: {consumption_result.data.get("point_count", 0)}')

      # Log timestamp range information
      if 'timestamp_range' in consumption_result.data:
        timestamp_range = consumption_result.data['timestamp_range']
        logging.info(
          f'Time window: {datetime.fromtimestamp(timestamp_range["start"])} '
          f'to {datetime.fromtimestamp(timestamp_range["end"])} '
          f'({timestamp_range["window_ms"] / 1000 / 60:.1f} minutes)'
        )

      return total_consumption
    else:
      logging.error(f'Failed to get current consumption: {consumption_result.error}')
      return 0.0

  @staticmethod
  def tst1():
    print('!!!!tst!!!!')
    return 10

  def register_base_report(self) -> None:
    """
    Register the base report for the Virtual End Node (VEN).

    :raises Exception: If an error occurs during the registration process.
    """
    try:
      if not self._open_adr_client:
        raise ValueError('OpenADR client not initialized')

      if not self._base_event_registered:
        logging.info('Registering base report')
        report: List[ReportConfig] = [
          ReportConfig(
            report_type=enums.REPORT_TYPE.USAGE,
            reading_type=enums.READING_TYPE.SUMMED,
            resource_id=BASE_RESOURCE_ID,
            measurement='power',
            sampling_rate=timedelta(seconds=10),
            callback=self._get_current_consumption,
          )
        ]
        self.add_reports(report)
        self._base_event_registered = True
        logging.info('Base report registered successfully')
    except ValueError as e:
      logging.error(f'OpenADR client initialization failed: {str(e)}')
      self._base_event_registered = False
      raise
    except TypeError as e:
      logging.error(
        f'Invalid base report configuration - Check measurement type and sampling rate: {str(e)}'
      )
      self._base_event_registered = False
      raise
    except (ConnectionError, TimeoutError) as e:
      logging.error(
        f'Network error while registering base report - Check VTN connectivity: {str(e)}'
      )
      self._base_event_registered = False
      raise
    except Exception as e:
      logging.error(f'Failed to register base report: {e}')
      raise

  def get_data(self) -> float:
    """
    Get the base consumption data.

    :return: Base consumption data.
    :rtype: float
    """
    logging.info('Getting base consumption data')
    return self._base_consumption

  def add_reports(self, reports: Optional[List[ReportConfig]] = None) -> None:
    """
    Add reports to the OpenADR client.

    :param reports: List of report configurations.
    :type reports: Optional[List[ReportConfiguration]]
    """
    if reports:
      for report in reports:
        if not report.resource_id or not report.measurement:
          logging.error(f'Invalid report configuration: {report}')
          continue

        if not report.callback:
          logging.error(f'Missing callback for report: {report}')
          continue

        report.report_type = report.report_type or enums.REPORT_TYPE.USAGE
        report.reading_type = report.reading_type or enums.READING_TYPE.DIRECT_READ
        wrapped_callback = self._wrap_callback(report.callback, report)

        self._open_adr_client.add_report(
          resource_id=report.resource_id,
          measurement=report.measurement,
          sampling_rate=report.sampling_rate,
          callback=wrapped_callback,
        )
        logging.info(f'Successfully added report for resource: {report.resource_id}')
    logging.info('Reports added to OpenADR client')

  async def handle_event(self, event: Dict[str, Any]) -> str:
    print('!!!Processing OpenADR event!!!')
    logging.info(f'[{datetime.now(timezone.utc).isoformat()}] Processing OpenADR event')
    required_keys = {
      'event_descriptor',
      'active_period',
      'event_signals',
      'targets',
    }
    if not all(key in event for key in required_keys):
      raise KeyError(f'Event missing required fields: {required_keys}')

    _event_descriptor = event['event_descriptor']
    _active_period = event['active_period']
    _event_signals = event['event_signals']
    _targets = event['targets']

    if not isinstance(_event_signals, list) or not all(
      isinstance(signal, dict) for signal in _event_signals
    ):
      raise ValueError('Invalid event_signals format')

    flattened_intervals = [
      {
        'dtstart': interval['dtstart'],
        'duration': interval['duration'],
        'signal_payload': interval['signal_payload'],
      }
      for signal in _event_signals
      for interval in signal.get('intervals', [])
      if 'dtstart' in interval
      and 'duration' in interval
      and 'signal_payload' in interval
    ]

    if not flattened_intervals:
      raise ValueError('No valid intervals found in event_signals')

    self._load_profile_service.save_load_profile(flattened_intervals)
    return 'optIn'
