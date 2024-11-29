import asyncio
import multiprocessing
import os
from typing import Optional, List, Any, Dict
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv

from src.mock_node.fe import SimpleGradioApp
from src.openadr_node.async_event_bus import dispatcher as dispatcher
from src.openadr_node.models import ReportConfiguration, EventSignal, Interval
from src.openadr_node.virtual_end_node import VirtualEndNode
from src.openadr_node.virtual_top_node import VirtualTopNode


class NodeManager:
    def __init__(self, vtn_name: Optional[str] = None, ven_name: Optional[str] = None,
                 vtn_url: Optional[str] = None):
        self._vtn_name: Optional[str] = vtn_name
        self._ven_name: Optional[str] = ven_name
        self._vtn_url: Optional[str] = vtn_url

        # Replace pydispatch topics with asyncio queue
        self._topics_queue = asyncio.Queue()
        self._topics: Dict[str, Dict[str, Any]] = {}

        # Create an event for signaling updates
        self._load_profile_update_event = asyncio.Event()

        # Create the event loop and tasks
        self._loop = asyncio.get_event_loop()
        self._create_node_tasks()

        self._queue = multiprocessing.Queue()

        # Start a background task to process topic updates
        self._loop.create_task(self._process_topic_updates())

        print("BEFORE INIT")
        dispatcher.subscribe('on_update_load_profile', self.tst)

    @staticmethod
    async def tst(sender=None, **kwargs):
        # Update chart or UI based on the event data
        print("Load profile updated:", kwargs.get('data'))
        #data = kwargs.get('data', None)


    async def _process_topic_updates(self):
        """Background task to process topic updates from the queue."""
        while True:
            update = await self._topics_queue.get()
            try:
                topic, subtopic, value = update
                if topic not in self._topics:
                    self._topics[topic] = {}
                self._topics[topic][subtopic] = value

                # If the update is for load profile, set the event
                if topic == 'ui' and subtopic == 'update_load_profile':
                    print("Load profile updated in NodeManager")
                    print("Received data:", value)
                    self._load_profile_update_event.set()
                    await self._dispatch_adr_event()
            finally:
                self._topics_queue.task_done()

    def set_topic_value(self, topic: str, subtopic: str, value: Any) -> None:
        """Put topic update into the queue for async processing."""
        self._loop.create_task(self._topics_queue.put((topic, subtopic, value)))

    def get_topic_value(self, topic: str, subtopic: str) -> Optional[Any]:
        """Retrieve topic value synchronously."""
        return self._topics.get(topic, {}).get(subtopic)

    def _create_node_tasks(self):
        if self._vtn_name:
            self._vtn = VirtualTopNode(self._vtn_name)
            self._loop.create_task(self._vtn.get_open_adr_server_run())

        if self._ven_name and self._vtn_url:
            self._ven = VirtualEndNode(self._ven_name, self._vtn_url, self._update_manager)
            self._loop.create_task(self._ven.get_open_adr_server_run())

    async def _dispatch_adr_event(self):
        """Dispatch ADR event when load profile is updated."""
        print("Dispatching ADR event")
        event = EventSignal(
            ven_id="ven_id_123",
            signal_name="simple",
            signal_type="level",
            intervals=[
                Interval(
                    dtstart=datetime(2021, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                    duration=timedelta(minutes=10),
                    signal_payload=1
                )
            ],
            callback=self._event_response_callback
        )
        await self._vtn.dispatch_adr_event(event)

    @staticmethod
    def _event_response_callback(self, data: Dict[str, Any]) -> None:
        print("Event response callback")

    def add_task(self, task):
        """Add a task to the event loop."""
        self._loop.create_task(task())
        #process = multiprocessing.Process(target=task, args=([self._queue]))
        #process.start()

    def run_node(self):
        """Run the event loop."""
        self._loop.run_forever()

    def _update_manager(self, data: Any):
        """Update manager with received data."""
        print(data)
        self.set_topic_value('report', 'update', data)

    def add_report(self, list_of_reports: Optional[List[ReportConfiguration]] = None):
        """Add reports to the VEN."""
        self._ven.add_reports(list_of_reports)


async def run_node_frontend():
    """Run Streamlit frontend as a subprocess."""
    current_dir = os.getcwd()
    script_path = os.path.join(current_dir, 'addons\streamlit.py')

    process = await asyncio.create_subprocess_exec('streamlit', 'run', script_path)
    await process.wait()


def main():
    """Main function to set up and run the node manager."""
    load_dotenv()
    print(id(dispatcher))

    node_manager = NodeManager(
        vtn_name=os.getenv('SERVER_NAME'),
        # ven_name=os.getenv('VEN_NAME'),
        # vtn_url=os.getenv('VTN_URL'),
    )
    print(id(dispatcher))

    simple_gradio = SimpleGradioApp()
    node_manager.add_task(simple_gradio.launch_interface)
    node_manager.run_node()


if __name__ == '__main__':
    main()
