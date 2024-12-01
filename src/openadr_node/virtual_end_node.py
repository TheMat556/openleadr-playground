from typing import Optional, List

from openleadr import OpenADRClient

from src.openadr_node.models import ReportConfiguration


class VirtualEndNode:
  def __init__(self, ven_name: str, vtn_url: str):
    self._ven_name = ven_name
    self._vtn_url = vtn_url
    self._open_adr_client = OpenADRClient(self._ven_name, self._vtn_url)
    self._init_default_handler()

  def  _init_default_handler(self):
    self._open_adr_client.add_handler('on_event', self.handle_event)

  def add_reports(self, reports: Optional[List[ReportConfiguration]] = None):
    print(reports)
    if reports:
      for report in reports:
        print("report callback", report.callback)

        self._open_adr_client.add_report(
          resource_id=report.resource_id,
          measurement=report.measurement,
          sampling_rate=report.sampling_rate,
          callback=report.callback,
        )

  @staticmethod
  async def handle_event(event):
    # business logic
    # handle event
    print("DISPATCHING EVENT MUST BE HANDLED!!!")
    _event_descriptor = event['event_descriptor']
    _active_period = event['active_period']
    _event_signals = event['event_signals']
    _targets = event['targets']
    return 'optIn'  # eventually pass devices status?

  def get_open_adr_server_run(self):
    return self._open_adr_client.run()
