import asyncio
import sys
from injector import Injector
from src.openadr_node import logger
from src.openadr_node.dependency_injection.modules import ApplicationModule
from src.openadr_node.config.app_config import ApplicationConfig
from src.openadr_node.protocols.mqtt.config.mqtt_config import MQTTConfig
from src.openadr_node.models.rest_config import RestApiConfig
from src.openadr_node.models.topic_config import TopicConfig, TopicType
from src.openadr_node.node_controller import NodeController


async def main() -> None:
  """Main entry point for the OpenADR node application"""
  try:
    # Initialize configuration
    config = create_application_config()

    # Set up dependency injection
    injector = Injector([ApplicationModule(config)])
    print('INJECTOR', injector)
    # Get NodeController instance with all dependencies injected
    node_controller = injector.get(NodeController)

    # Run the application
    logger.info('Starting OpenADR node application...')
    await node_controller.run()

  except KeyboardInterrupt:
    logger.info('Application shutdown requested')
  except Exception as e:
    logger.error(f'Application error: {e}')
    sys.exit(1)


def create_application_config() -> ApplicationConfig:
  """Create and return application configuration"""
  try:
    topic_config = [
      TopicConfig('load_profile', topic_type=TopicType.PUBLISH),
      TopicConfig('consumption', topic_type=TopicType.SUBSCRIBE),
    ]
    # You might want to load these from environment variables or config file
    mqtt_config = MQTTConfig(
      broker='localhost',
      port=1883,
      username='user',
      password='pass',
      topics=topic_config,
      client_id='openadr_node',
    )

    rest_config = RestApiConfig(
      port=5000,
    )

    return ApplicationConfig(
      node_id='node1',
      vtn_name='vtn1',
      ven_name='ven1',
      vtn_url='http://localhost:8080',
      openadr_http_host='localhost',
      openadr_http_port=8080,
      openadr_vtn_path_prefix='/OpenADR2/Simple/2.0b',
      mqtt_config=mqtt_config,
      flask_app_service=rest_config,
    )
  except Exception as e:
    logger.error(f'Failed to create application config: {e}')
    raise


if __name__ == '__main__':
  asyncio.run(main())
