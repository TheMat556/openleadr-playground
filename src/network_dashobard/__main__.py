import os
import argparse
from pathlib import Path

import logging
from dependency_injector.wiring import inject, Provide

from src.network_dashobard.config.app_config import AppConfig
from src.network_dashobard.implementations.dashboard import GradioNodeDashboard
from .di.container import Container
from .helper.constants import UISettings


class DashboardApp:
  def __init__(self):
    self.container = Container()
    self.dashboard = None

  def setup_container(self, config_path: str) -> None:
    """Sets up the dependency injection container"""
    try:
      # Load configuration
      app_config = AppConfig.from_file(config_path)

      # Configure container
      self.container.config.from_dict(
        {
          'config_path': config_path,
          'max_buffer_size': app_config.max_buffer_size,
          'update_interval': app_config.update_interval,
          'environment': app_config.environment,
          'configs': app_config.node_configs,
        }
      )

      # Wire dependencies
      self.container.wire(modules=[__name__])

    except Exception as e:
      logging.error(f'Failed to setup container: {e}')
      raise

  @inject
  def create_dashboard(
    self, dashboard: GradioNodeDashboard = Provide[Container.dashboard]
  ) -> None:
    """Creates the dashboard instance"""
    self.dashboard = dashboard

  def run(
    self,
    server_name: str = '0.0.0.0',
    server_port: int = UISettings.DEFAULT_PORT,
    share: bool = False,
  ) -> None:
    """Runs the dashboard application"""
    try:
      if not self.dashboard:
        raise RuntimeError('Dashboard not created. Call create_dashboard first.')

      interface = self.dashboard.create_interface()
      interface.queue()
      interface.launch(
        server_name=server_name,
        server_port=server_port,
        share=share,
        favicon_path=str(Path(__file__).parent / 'assets' / 'favicon.ico'),
      )

    except Exception as e:
      logging.error(f'Failed to run dashboard: {e}')
      raise


def parse_args() -> argparse.Namespace:
  """Parses command line arguments"""
  parser = argparse.ArgumentParser(description='Node Dashboard Application')
  parser.add_argument(
    '--config',
    type=str,
    default='./config/config.json',
    help='Path to configuration file',
  )
  parser.add_argument(
    '--port',
    type=int,
    default=UISettings.DEFAULT_PORT,
    help='Port to run the server on',
  )
  parser.add_argument(
    '--host', type=str, default='0.0.0.0', help='Host to run the server on'
  )
  parser.add_argument('--share', action='store_true', help='Create a public URL')
  return parser.parse_args()


def main() -> None:
  """Main entry point for the application"""
  try:
    # Parse command line arguments
    args = parse_args()

    # Set up logging
    os.makedirs('logs', exist_ok=True)
    logging.info('Starting Node Dashboard application...')

    # Create and configure the application
    app = DashboardApp()
    app.setup_container(args.config)
    app.create_dashboard()

    # Run the application
    logging.info(f'Launching dashboard on {args.host}:{args.port}')
    app.run(server_name=args.host, server_port=args.port, share=args.share)

  except Exception as e:
    logging.error(f'Application failed to start: {e}')
    raise


if __name__ == '__main__':
  main()
