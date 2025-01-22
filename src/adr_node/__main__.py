import signal
import sys
import time  # New import for time.sleep
from datetime import datetime, timezone

from dependency_injector import containers, providers
from src.adr_node.communication.rest.services.rest_service import RestService
from src.adr_node.core.controller.node_component_controller import (
  NodeComponentController,
)
from src.openadr_node.adr_logger.logger import logger


class Container(containers.DeclarativeContainer):
  wiring_config = containers.WiringConfiguration(modules=['__main__'])

  # Configuration
  config = providers.Configuration()

  # Set default configuration values
  config.from_dict({'rest': {'host': 'localhost', 'port': 5000}})

  # Services
  rest_service = providers.Singleton(
    RestService, host=config.rest.host, port=config.rest.port
  )

  # Controllers
  node_controller = providers.Singleton(
    NodeComponentController, rest_service=rest_service
  )


def signal_handler(sig, frame):
  logger.info('Received shutdown signal. Initiating graceful shutdown...')
  controller.stop()
  sys.exit(0)  # Exit the application gracefully


if __name__ == '__main__':
  try:
    # Log startup time using timezone-aware datetime
    startup_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    logger.info(f'Application starting at (UTC): {startup_time}')

    # Create and configure the container
    container = Container()

    # Get the controller from the container
    controller = container.node_controller()

    # Setup signal handling
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the controller
    controller.start()
    logger.info('Node controller started successfully')

    # Keep the main thread alive using an infinite loop
    while True:
      time.sleep(1)  # Sleep for 1 second to prevent CPU overuse
  except Exception as e:
    logger.error(f'Failed to start application: {str(e)}')
    sys.exit(1)
