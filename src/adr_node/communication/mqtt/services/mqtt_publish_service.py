from typing import Any, Dict
import json
import logging
from datetime import datetime

from src.adr_node.communication.mqtt.interfaces.imqtt_publish_service import (
    IMQTTPublishService,
)
from src.adr_node.communication.mqtt.services.mqtt_connection_service import (
    MQTTConnectionService,
)
from src.adr_node.database.services.core.load_profile_service import LoadProfileService
from src.adr_node.event_bus.decorators.init_signal_handlers import init_signal_handlers
from src.adr_node.event_bus.interfaces.ievent_bus import IEventBus
from src.adr_node.event_bus.decorators.handle_signal import handle_signal
from src.adr_node.event_bus.constants.signal_types import SignalType


class MQTTPublishService(IMQTTPublishService):
    def __init__(
        self,
        connection_handler: MQTTConnectionService,
        load_profile_service: LoadProfileService,
        event_bus: IEventBus,
        publish_interval: int = 60,
    ):
        self.connection_handler = connection_handler
        self.load_profile_service = load_profile_service
        self.event_bus = event_bus
        self.publish_interval = publish_interval
        self.last_publish: Dict[str, datetime] = {}
        init_signal_handlers(self)

    def publish(self, topic: str, payload: Any) -> None:
        """Synchronous publish method for direct calls"""
        try:
            self.connection_handler.client.publish(topic, json.dumps(payload))
            logging.debug(f"Published to {topic}: {payload}")
        except Exception as e:
            logging.error(f"Failed to publish to {topic}: {e}")

    def _get_load_profile_payload(
        self, current_time: datetime
    ) -> Dict[str, Any] | None:
        unix_timestamp = int(current_time.timestamp())
        load_profile_point = self.load_profile_service.get_closest_load_point(
            unix_timestamp
        )

        if not load_profile_point or not all(
            key in load_profile_point
            for key in ["dstart", "duration", "signal_payload"]
        ):
            return None

        return {
            "timestamp": load_profile_point["dstart"],
            "load_profile": load_profile_point["signal_payload"],
        }

    def _should_publish(self, topic: str) -> bool:
        if topic not in self.last_publish:
            return True

        time_since_last = (datetime.now() - self.last_publish[topic]).total_seconds()
        return time_since_last >= self.publish_interval

    def handle_periodic_publish(self, topic: str) -> None:
        if topic != "load-profile" or not self._should_publish(topic):
            return

        try:
            current_time = datetime.now()
            payload = self._get_load_profile_payload(current_time)

            if payload:
                self.publish(topic, payload)
                self.last_publish[topic] = current_time

        except Exception as e:
            logging.error(f"Error in periodic publish for topic {topic}: {e}")

    @handle_signal(SignalType.LOAD_DISTRIBUTION_UPDATED)
    def on_load_distribution_updated(self, sender: str) -> None:
        try:
            current_time = datetime.now()
            payload = self._get_load_profile_payload(current_time)

            if payload:
                self.publish("load-profile", payload)
                self.last_publish["load-profile"] = current_time

        except Exception as e:
            logging.error(f"Error handling LOAD_DISTRIBUTION_UPDATED signal: {e}")
