from datetime import timedelta
from typing import Optional, List, Dict, Any

from openleadr import OpenADRClient

from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.decorator.signal_connector import SignalConnector
from src.openadr_node.decorator.signal_sender import SignalSender
from src.openadr_node.models import ReportConfiguration
from src.openadr_node import logger


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
    self._base_event_registered = False  # Flag to track if base event is registered
    self._base_consumption = 0.0

  def _init_default_handler(self) -> None:
    """
    Initialize the default event handler for the OpenADR client.
    """
    self._open_adr_client.add_handler('on_event', self.handle_event)

  def get_open_adr_server_run(self) -> Any:
    """
    Get the OpenADR server run method.

    :return: The run method of the OpenADR client.
    :rtype: Any
    """
    return self._open_adr_client.run()

  def register_base_report(self) -> None:
    """
    Register the base report for the Virtual End Node (VEN).

    :raises Exception: If an error occurs during the registration process.
    """
    try:
      if not self._base_event_registered:
        logger.info('Registering base report')
        report: List[ReportConfiguration] = [
          ReportConfiguration(
            resource_id='base',
            measurement='energy',
            sampling_rate=timedelta(seconds=5),
            callback=self.get_data,
          )
        ]
        self.add_reports(report)
        self._base_event_registered = True  # Set the flag to True after registering
        logger.info('Base report registered successfully')
    except Exception as e:
      logger.error(f'Failed to register base report: {e}')
      raise

  def get_data(self) -> float:
    """
    Get the current base consumption data.

    :return: The current base consumption.
    :rtype: float
    """
    logger.info('Getting base consumption data')
    return self._base_consumption

  @SignalSender('add_reports', 'ven')
  def add_reports(self, reports: Optional[List[ReportConfiguration]] = None) -> None:
    """
    Add reports to the OpenADR client.

    :param reports: List of report configurations.
    :type reports: Optional[List[ReportConfiguration]]
    """
    if reports:
      for report in reports:
        self._open_adr_client.add_report(
          resource_id=report.resource_id,
          measurement=report.measurement,
          sampling_rate=report.sampling_rate,
          callback=report.callback,
        )
    logger.info('Reports added to OpenADR client')

  @SignalSender('handle_event', 'ven')
  def handle_event(self, event: Dict[str, Any]) -> str:
    """
    Handle OpenADR event and update load profile.

    :param event: OpenADR event containing event_signals, each with intervals
                  defining dtstart, duration, and signal_payload.
    :type event: Dict[str, Any]
    :return: Response status ('optIn' or 'optOut')
    :rtype: str
    :raises KeyError: If required event fields are missing
    :raises ValueError: If event_signals format is invalid or no valid intervals found
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
    return 'optIn'  # eventually pass devices status?

  @SignalSender('update_load_profile', 'ven')
  def update_load_profile(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Update the load profile with the given data.

    :param data: List of intervals with dtstart, duration, and signal_payload.
    :type data: List[Dict[str, Any]]
    :return: The updated load profile data.
    :rtype: List[Dict[str, Any]]
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
    :param data: The new base consumption data.
    :type data: float
    """
    logger.info(f'Updating base consumption data: {data}')
    self._base_consumption = data
