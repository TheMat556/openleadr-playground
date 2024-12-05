from typing import Optional, List

from openleadr import OpenADRClient

from src.openadr_node.adr_base_config import AdrBaseConfig
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

  def _init_default_handler(self):
    self._open_adr_client.add_handler('on_event', self.handle_event)

  def get_open_adr_server_run(self):
    return self._open_adr_client.run()

  @SignalSender('add_reports', 'ven')
  def add_reports(self, reports: Optional[List[ReportConfiguration]] = None):
    if reports:
      for report in reports:
        self._open_adr_client.add_report(
          resource_id=report.resource_id,
          measurement=report.measurement,
          sampling_rate=report.sampling_rate,
          callback=report.callback,
        )

  @SignalSender('handle_event', 'ven')
  def handle_event(self, event):
    # business logic
    # handle event
    print('DISPATCHING ACTION GOTTEN')
    logger.info('Processing openADR Event')
    _event_descriptor = event['event_descriptor']
    _active_period = event['active_period']
    _event_signals = event['event_signals']
    _targets = event['targets']
    print('EVENT!!')
    return 'optIn'  # eventually pass devices status?
