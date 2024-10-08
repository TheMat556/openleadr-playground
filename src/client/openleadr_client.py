import string
from datetime import timedelta
import logging

from openleadr import OpenADRClient, enable_default_logging

from src.openleadr_node.dependencies.venInterface import VenDependencyInterface

enable_default_logging()
logger = logging.getLogger(__name__)


class OpenLeADRClient:
  def __init__(
    self, ven_name: string, vtn_url: string, controller: VenDependencyInterface
  ):
    self.client = OpenADRClient(ven_name=ven_name, vtn_url=vtn_url)

    self.client.add_report(
      callback=self.collect_report_value,
      resource_id='device001',
      measurement='voltage',
      sampling_rate=timedelta(seconds=10),
    )

    # Add event handling capability to the client
    self.client.add_handler('on_event', self.handle_event)
    self.controller = controller

  async def collect_report_value(self):
    # This callback is called when you need to collect a value for your Report
    value = self.controller.handle_collect_report_value()
    return value

  async def handle_event(self, event):
    # This callback receives an Event dict.
    # You should include code here that sends control signals to your resources.
    _event_descriptor = event['event_descriptor']
    _active_period = event['active_period']
    _event_signals = event['event_signals']
    _targets = event['targets']
    return 'optIn'
