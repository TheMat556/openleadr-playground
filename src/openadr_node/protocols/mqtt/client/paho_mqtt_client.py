# protocols/mqtt/client/paho_mqtt_client.py
import ssl
import time
import paho.mqtt.client as mqtt

from src.openadr_node import logger
from src.openadr_node.protocols.helper.manager_state import MQTTState
from src.openadr_node.protocols.mqtt.config.mqtt_config import MQTTConfig
from src.openadr_node.protocols.mqtt.interfaces.mqtt_interface import IMQTTClient


class PahoMQTTClient(IMQTTClient):
  def __init__(self, config: MQTTConfig):
    self.config = config
    self._state = MQTTState()

    # Initialize client
    client_id = f'{config.client_id_prefix}_{int(time.time())}'
    self._client = mqtt.Client(client_id=client_id, clean_session=True)
    self._configure_client()

  def _configure_client(self) -> None:
    """Configure the MQTT client with TLS and authentication"""
    try:
      self._client.username_pw_set(self.config.username, self.config.password)

      if self.config.use_tls:
        self._client.tls_set(
          ca_certs=self.config.ca_certs, tls_version=ssl.PROTOCOL_TLSv1_2
        )
        self._client.tls_insecure_set(False)

      self._client.on_connect = self._on_connect
      self._client.on_disconnect = self._on_disconnect
      self._client.on_message = self._on_message
    except Exception as e:
      logger.error(f'Failed to configure MQTT client: {e}')
      raise

  async def connect(self) -> None:
    """Connect to the MQTT broker"""
    try:
      self._client.connect_async(
        self.config.broker, self.config.port, keepalive=self.config.keepalive
      )
      self._client.loop_start()
    except Exception as e:
      logger.error(f'Failed to connect to MQTT broker: {e}')
      raise

  async def disconnect(self) -> None:
    """Disconnect from the MQTT broker"""
    try:
      self._client.disconnect()
      self._client.loop_stop()
    except Exception as e:
      logger.error(f'Failed to disconnect from MQTT broker: {e}')
      raise
