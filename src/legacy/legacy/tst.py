import asyncio
import logging
from typing import List, Dict, Any

from openleadr import OpenADRClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProxyVTN:
  def __init__(self, primary_vtn_url: str, secondary_vtn_url: str, ven_name: str):
    """
    Initialize Proxy VTN with multiple VTN connections

    :param primary_vtn_url: URL of the primary VTN
    :param secondary_vtn_url: URL of the secondary VTN
    :param ven_name: Name of the Virtual End Node
    """
    self.primary_vtn = OpenADRClient(
      ven_name=f'{ven_name}_primary', vtn_url=primary_vtn_url
    )

    self.secondary_vtn = OpenADRClient(
      ven_name=f'{ven_name}_secondary', vtn_url=secondary_vtn_url
    )

    self.ven_name = ven_name
    self.events_queue = asyncio.Queue()

  async def connect(self):
    """
    Establish connections with both VTNs
    """
    try:
      # Register with primary VTN
      await self.primary_vtn.create_party_registration()
      logger.info(f'Registered with primary VTN: {self.primary_vtn.vtn_url}')

      # Register with secondary VTN
      await self.secondary_vtn.create_party_registration()
      logger.info(f'Registered with secondary VTN: {self.secondary_vtn.vtn_url}')
    except Exception as e:
      logger.error(f'Registration error: {e}')
      raise

  async def poll_events(self):
    """
    Continuously poll events from both VTNs
    """
    while True:
      try:
        # Poll primary VTN for events
        primary_events = await self._get_vtn_events(self.primary_vtn)
        for event in primary_events:
          event['source'] = 'primary'
          await self.events_queue.put(event)

        # Poll secondary VTN for events
        secondary_events = await self._get_vtn_events(self.secondary_vtn)
        for event in secondary_events:
          event['source'] = 'secondary'
          await self.events_queue.put(event)

        # Wait before next polling cycle
        await asyncio.sleep(60)  # Poll every minute

      except Exception as e:
        logger.error(f'Error polling events: {e}')
        await asyncio.sleep(30)  # Wait before retrying

  async def _get_vtn_events(self, vtn_client: OpenADRClient) -> List[Dict[str, Any]]:
    """
    Retrieve events from a specific VTN

    :param vtn_client: OpenADR client for a specific VTN
    :return: List of events
    """
    try:
      # This is a conceptual method - actual implementation depends on OpenLEADR's API
      events = await vtn_client.request_events()
      return events
    except Exception as e:
      logger.warning(f'Error retrieving events from {vtn_client.vtn_url}: {e}')
      return []

  async def process_events(self):
    """
    Process events from the queue with custom logic
    """
    while True:
      event = await self.events_queue.get()
      try:
        logger.info(f"Processing event from {event['source']} VTN")

        # Custom event processing logic
        if event['source'] == 'primary':
          # Specific handling for primary VTN events
          await self._handle_primary_event(event)
        else:
          # Specific handling for secondary VTN events
          await self._handle_secondary_event(event)

        # Optional: Send opt-in/opt-out response
        await self._send_event_response(event)

      except Exception as e:
        logger.error(f'Event processing error: {e}')

      finally:
        self.events_queue.task_done()

  async def _handle_primary_event(self, event: Dict[str, Any]):
    """
    Custom logic for handling primary VTN events
    """
    # Example: Prioritize primary VTN events
    logger.info(f'Handling primary VTN event with priority: {event}')

  async def _handle_secondary_event(self, event: Dict[str, Any]):
    """
    Custom logic for handling secondary VTN events
    """
    # Example: Secondary VTN events might have different processing
    logger.info(f'Handling secondary VTN event: {event}')

  async def _send_event_response(self, event: Dict[str, Any]):
    """
    Send event response to the appropriate VTN
    """
    vtn_client = (
      self.primary_vtn if event['source'] == 'primary' else self.secondary_vtn
    )

    try:
      # Send opt-in status
      await vtn_client.send_opt_status(
        event_id=event.get('event_id', ''), opt_status='optIn'
      )
    except Exception as e:
      logger.error(f'Error sending event response: {e}')

  async def run(self):
    """
    Main run method to start proxy VTN operations
    """
    await self.connect()

    # Create tasks for polling and processing
    poll_task = asyncio.create_task(self.poll_events())
    process_task = asyncio.create_task(self.process_events())

    await asyncio.gather(poll_task, process_task)


async def main():
  # Example usage
  proxy_vtn = ProxyVTN(
    primary_vtn_url='https://primary-vtn.example.com',
    secondary_vtn_url='https://secondary-vtn.example.com',
    ven_name='MultiSourceVEN',
  )

  try:
    await proxy_vtn.run()
  except Exception as e:
    logger.error(f'Proxy VTN run error: {e}')


if __name__ == '__main__':
  asyncio.run(main())
