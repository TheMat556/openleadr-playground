from datetime import timedelta
from typing import Optional, List, Dict, Any

from openleadr import OpenADRClient

from src.openadr_node.adr_base_config import AdrBaseConfig
from src.openadr_node.decorator.signal_connector import SignalConnector
from src.openadr_node.decorator.signal_sender import SignalSender
from src.openadr_node.models import ReportConfiguration
from src.openadr_node import logger


class VirtualEndNode(AdrBaseConfig):
  def __init__(self, ven_name: str, vtn_url: str):
    super().__init__()
    self._ven_name = ven_name
    self._vtn_url = vtn_url
    self._open_adr_client = OpenADRClient(self._ven_name, self._vtn_url)
    self._init_default_handler()
    self._base_event_registered = False  # Flag to track if base event is registered
    self._base_consumption = 0

  def _init_default_handler(self) -> None:
    self._open_adr_client.add_handler('on_event', self.handle_event)

  def get_open_adr_server_run(self) -> Any:
    return self._open_adr_client.run()

  def register_base_report(self) -> None:
    print('Registering base event')
    if not self._base_event_registered:
      report: List[ReportConfiguration] = [ReportConfiguration(
        resource_id='base',
        measurement='energy',
        sampling_rate=timedelta(seconds=5),
        callback=self.get_data,  # lambda: self._base_consumption,
      )]
      self.add_reports(report)
      self._base_event_registered = True  # Set the flag to True after registering
      print('Registered REport succ!')

  def get_data(self) -> float:
    print('GET_DATA')
    return self._base_consumption

  #@SignalSender('add_reports', 'ven')
  def add_reports(self, reports: Optional[List[ReportConfiguration]] = None) -> None:
    print("Step1")
    if reports:
      print("Step2")
      for report in reports:
        print("Step3")
        self._open_adr_client.add_report(
          resource_id=report.resource_id,
          measurement=report.measurement,
          sampling_rate=report.sampling_rate,
          callback=report.callback,
        )
    return None

  @SignalSender('handle_event', 'ven')
  def handle_event(self, event: Dict[str, Any]) -> str:
    """Handle OpenADR event and update load profile.

    Args:
        event (Dict[str, Any]): OpenADR event containing event_signals, each with intervals
            defining dtstart, duration, and signal_payload.

    Returns:
        str: Response status ('optIn' or 'optOut')

    Raises:
        KeyError: If required event fields are missing
    """
    logger.info('Processing openADR Event')
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
    return data

  @SignalConnector('update_consumption_data', 'nm')
  def _on_update_consumption_data(self, sender: str, signal: str, data: float) -> None:
    print('VEN - _on_update_consumption_data', data)
    self._base_consumption = data
