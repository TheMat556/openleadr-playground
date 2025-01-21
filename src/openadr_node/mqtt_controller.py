import time
import json
import paho.mqtt.client as mqtt

from src.openadr_node.protocols.mqtt.config.mqtt_config import MQTTConfig


class MQTTManager:
  def __init__(self, config: MQTTConfig):
    """Initialize MQTT controller with given configuration.

    Args:
        config: MQTTConfig object containing connection details
    """
    print('CONFIG', config)
    self.config = config
    self.client = mqtt.Client(client_id=config.client_id)
    self.running = False
    self._setup_client()

  def _setup_client(self) -> None:
    """Configure MQTT client with credentials and TLS if needed."""
    # Set username and password
    self.client.username_pw_set(self.config.username, self.config.password)

    # Configure TLS if enabled
    if self.config.use_tls:
      if self.config.ca_certs:
        self.client.tls_set(ca_certs=self.config.ca_certs)
      else:
        self.client.tls_set()

    # Set up callbacks
    self.client.on_connect = self._on_connect
    self.client.on_disconnect = self._on_disconnect

  def _on_connect(self, client, userdata, flags, rc):
    """Callback for when the client connects to the broker."""
    if rc == 0:
      print('Successfully connected to MQTT broker')
    else:
      print(f'Failed to connect to MQTT broker with code: {rc}')

  def _on_disconnect(self, client, userdata, rc):
    """Callback for when the client disconnects from the broker."""
    print('Disconnected from MQTT broker')

  def start(self):
    """Start the MQTT controller and begin publishing data."""
    if not self.config.is_valid():
      raise ValueError('Invalid MQTT configuration')

    try:
      # Connect to broker
      self.client.connect(
        self.config.broker, self.config.port, keepalive=self.config.keepalive
      )

      # Start MQTT loop in a separate thread
      self.client.loop_start()
      self.running = True

    except Exception as e:
      print(f'Error starting MQTT controller: {e}')
      self.stop()

  def stop(self):
    """Stop the MQTT controller and clean up resources."""
    self.running = False
    if hasattr(self, 'publish_thread'):
      self.publish_thread.join(timeout=1)
    self.client.loop_stop()
    self.client.disconnect()

  def _publish_loop(self):
    """Main publishing loop that runs every 5 seconds."""
    while self.running:
      try:
        # Publish to all configured topics
        if self.config.topics:
          for topic in self.config.topics:
            # Example data - replace with your actual data
            data = {
              'timestamp': time.time(),
              'value': 42,  # Replace with your actual data
              'topic': topic.topic,
            }

            self.client.publish(
              topic.topic,
              json.dumps(data),
              qos=topic.qos if hasattr(topic, 'qos') else 0,
            )
            print(f'Published to {topic.topic}: {data}')

        # Wait for 5 seconds
        time.sleep(5)

      except Exception as e:
        print(f'Error in publish loop: {e}')
        time.sleep(5)  # Wait before retrying
