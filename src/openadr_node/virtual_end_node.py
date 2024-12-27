from datetime import timedelta, datetime, timezone
from typing import Optional, List, Dict, Any, Callable, Tuple
from functools import wraps

from openleadr import OpenADRClient

from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.decorator.signal_connector import SignalConnector
from src.openadr_node.decorator.signal_sender import SignalSender
from src.openadr_node.models import ReportConfiguration
from src.openadr_node import logger
from src.openadr_node.models.event import ResourceConsumption

BASE_RESOURCE_ID = 'base'


class VirtualEndNode(AdrBaseConfig):
  """
  Represents a Virtual End Node (VEN) in the OpenADR system.
  """

  def __init__(self, ven_name: str, vtn_url: str):
    """
    Initialize the VirtualEndNode.

    :param ven_name: Name of the Virtual End Node.
    :type ven_name: str
    :param vtn_url: URL of the Virtual Top Node.
    :type vtn_url: str
    """
    super().__init__()
    self._ven_name = ven_name
    self._vtn_url = vtn_url
    self._open_adr_client = OpenADRClient(self._ven_name, self._vtn_url)
    self._init_default_handler()
    self._base_event_registered = False
    self._base_consumption = 0.0

  def _init_default_handler(self) -> None:
    """
    Initialize the default event handler for the OpenADR client.
    """
    self._open_adr_client.add_handler('on_event', self.handle_event)

  def get_open_adr_server_run(self) -> Any:
    """
    Get the OpenADR server run method.

    :return: The OpenADR server run method.
    :rtype: Any
    """
    return self._open_adr_client.run()

  def _wrap_callback(
    self, callback: Callable[..., float], resource_id: str
  ) -> Callable[..., float]:
    """
    Wrap a callback to include a timestamp with the result.
    :param callback: The callback function.
    :type callback: Callable[..., float]
    :param resource_id: Resource ID.
    :type resource_id: str
    :return: Wrapped callback function.
    :rtype: Callable[..., float]
    """

    @wraps(callback)
    def wrapper(*args, **kwargs):
      if callable(callback):
        timestamp = datetime.now(timezone.utc)  # Capture time before execution
        result = callback(*args, **kwargs)
        if result is None:
          logger.warning(f'Callback for resource {resource_id} returned None')
          return 0.0
        if not isinstance(result, (int, float)):
          logger.error(
            f'Callback for resource {resource_id} returned non-numeric value: {result}'
          )
          return 0.0
        timestamped_result = (timestamp, float(result))
        self._send_consumption_data(
          ven_id=self._ven_name, resource_id=resource_id, data=timestamped_result
        )
        return result
      return 0.0

    return wrapper

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
        report: List[ReportConfiguration] = [
          ReportConfiguration(
            resource_id='base',
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

  @SignalSender(signal='update_consumption_data', sender='vtn')
  def _send_consumption_data(
    self, ven_id: str, resource_id: str, data: Tuple[datetime, float]
  ) -> ResourceConsumption:
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

  def add_reports(self, reports: Optional[List[ReportConfiguration]] = None) -> None:
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
        callback = (
          self._wrap_callback(report.callback, report.resource_id)
          if report.resource_id != BASE_RESOURCE_ID
          else report.callback
        )
        self._open_adr_client.add_report(
          resource_id=report.resource_id,
          measurement=report.measurement,
          sampling_rate=report.sampling_rate,
          callback=callback,
        )
        logger.debug(f'Successfully added report for resource: {report.resource_id}')
    logger.info('Reports added to OpenADR client')

  def handle_event(self, event: Dict[str, Any]) -> str:
    """
    Handle an OpenADR event.

    :param event: The event data.
    :type event: Dict[str, Any] containing event_descriptor, active_period, event_signals, and targets
    :return: Response to the event.
    :rtype: str ('optIn', 'optOut', or 'optIn with override')
    :raises KeyError: If the event is missing required fields.
    :raises ValueError: If the event signals format is invalid.
    """
    logger.info('Processing OpenADR event')
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

  @SignalSender('update_load_profile', 'ven')
  def update_load_profile(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Update the load profile.

    :param data: The load profile data.
    :type data: List[Dict[str, Any]] containing dtstart, duration, and signal_payload
    :return: Updated load profile data.
    :rtype: List[Dict[str, Any]] with processed load profile information
    """
    logger.info('Updating load profile')
    return data

  @SignalConnector('update_consumption_data', 'nm')
  def _on_update_consumption_data(self, sender: str, signal: str, data: float) -> None:
    """
    Update the base consumption data.

    :param sender: The sender of the signal.
    :type sender: str
    :param signal: The signal name.
    :type signal: str
    :param data: The consumption data.
    :type data: float
    """
    logger.info(f'Updating base consumption data: {data}')
    self._base_consumption = data
