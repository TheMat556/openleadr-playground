from datetime import timezone, datetime, timedelta
from typing import Any, List, Tuple, Optional, Dict

from src.adr_node.config.report_config import ReportConfig
from src.adr_node.core.nodes.configs.virtual_end_node_config import VirtualEndNodeConfig
from src.adr_node.core.nodes.domains.resource_consumption import ResourceConsumption
from src.adr_node.core.nodes.interfaces.ivirtual_end_node import IVirtualEndNode
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus
from src.openadr_node import logger

BASE_RESOURCE_ID = 'base'


class VirtualEndNode(IVirtualEndNode):
  def __init__(self, config: VirtualEndNodeConfig, event_bus: IEventBus):
    super().__init__()
    self._ven_name = config.ven_name
    self._vtn_url = config.vtn_url
    self._open_adr_client = config.client_factory(self._ven_name, self._vtn_url)
    self._event_bus = event_bus
    self._init_default_handler()
    self._base_event_registered = False
    self._base_consumption = 0.0

  def run(self):
    return self._open_adr_client.run()

  def _init_default_handler(self) -> None:
    """
    Initialize the default event handler for the OpenADR client.
    """
    self._open_adr_client.add_handler('on_event', self.handle_event)

  def register_base_report(self) -> None:
    """
    Register the base report for the Virtual End Node (VEN).

    :raises Exception: If an error occurs during the registration process.
    """
    try:
      if not self._open_adr_client:
        raise ValueError('OpenADR client not initialized')

      if not self._base_event_registered:
        logger.info('Registering base report')
        report: List[ReportConfig] = [
          ReportConfig(
            resource_id=BASE_RESOURCE_ID,
            measurement='energy',
            sampling_rate=timedelta(seconds=5),
            callback=lambda: self._base_consumption,
          )
        ]
        self.add_reports(report)
        self._base_event_registered = True
        logger.info('Base report registered successfully')
    except ValueError as e:
      logger.error(f'OpenADR client initialization failed: {str(e)}')
      self._base_event_registered = False
      raise
    except TypeError as e:
      logger.error(
        f'Invalid base report configuration - Check measurement type and sampling rate: {str(e)}'
      )
      self._base_event_registered = False
      raise
    except (ConnectionError, TimeoutError) as e:
      logger.error(
        f'Network error while registering base report - Check VTN connectivity: {str(e)}'
      )
      self._base_event_registered = False
      raise
    except Exception as e:
      logger.error(f'Failed to register base report: {e}')
      raise

  def get_data(self) -> float:
    """
    Get the base consumption data.

    :return: Base consumption data.
    :rtype: float
    """
    logger.info('Getting base consumption data')
    return self._base_consumption

  def _send_consumption_data(
    self, ven_id: str, resource_id: str, data: Tuple[datetime, float]
  ) -> Any:
    """
    Send consumption data.

    :param ven_id: VEN ID.
    :type ven_id: str
    :param resource_id: Resource ID.
    :type resource_id: str
    :param data: Tuple of timestamp and consumption data.
    :type data: Tuple[datetime, float]
    :return: Resource consumption object.
    :rtype: ResourceConsumption
    """
    resource_consumption = ResourceConsumption(
      ven_id=ven_id, resource_id=resource_id, data=data
    )
    return resource_consumption

  def add_reports(self, reports: Optional[List[ReportConfig]] = None) -> None:
    """
    Add reports to the OpenADR client.

    :param reports: List of report configurations.
    :type reports: Optional[List[ReportConfiguration]]
    """
    if reports:
      for report in reports:
        if not report.resource_id or not report.measurement:
          logger.error(f'Invalid report configuration: {report}')
          continue
        logger.info(
          f'Adding report for resource: {report.resource_id}, measurement: {report.measurement}'
        )
        if not report.callback:
          logger.error(f'Missing callback for report: {report}')
          continue
        self._open_adr_client.add_report(
          resource_id=report.resource_id,
          measurement=report.measurement,
          sampling_rate=report.sampling_rate,
          callback=report.callback,
        )
        logger.debug(f'Successfully added report for resource: {report.resource_id}')
    logger.info('Reports added to OpenADR client')

  def handle_event(self, event: Dict[str, Any]) -> str:
    """
    Handle an OpenADR event.

    :param event: The event data.
    :type event: Dict[str, Any] containing event_descriptor, active_period, event_signals, and targets
    :return: Response to the event.
      - 'optIn': Accept the event as is
      - 'optOut': Decline to participate in the event
      - 'optIn with override': Accept with modifications
    :rtype: str ('optIn', 'optOut', or 'optIn with override')
    :raises KeyError: If the event is missing required fields.
    :raises ValueError: If the event signals format is invalid.
    """
    logger.info(f'[{datetime.now(timezone.utc).isoformat()}] Processing OpenADR event')
    required_keys = {'event_descriptor', 'active_period', 'event_signals', 'targets'}
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

    self.update_load_profile(flattened_intervals)
    return 'optIn'
