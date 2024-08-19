import asyncio
from datetime import timedelta
import logging

from openleadr import OpenADRClient, enable_default_logging

enable_default_logging()
logger = logging.getLogger(__name__)

class OpenLeADRClient:
    def __init__(self, ven_name, vtn_url):
        self.client = OpenADRClient(ven_name=ven_name, vtn_url=vtn_url)

        self.client.add_report(
            callback=self.collect_report_value,
            resource_id="device001",
            measurement="voltage",
            sampling_rate=timedelta(seconds=10),
        )

        # Add event handling capability to the client
        self.client.add_handler("on_event", self.handle_event)

    async def collect_report_value(self):
        # This callback is called when you need to collect a value for your Report
        return 1.23

    async def handle_event(self, event):
        # This callback receives an Event dict.
        # You should include code here that sends control signals to your resources.
        event_descriptor = event['event_descriptor']
        active_period = event['active_period']
        event_signals = event['event_signals']
        targets = event['targets']
        return "optIn"