import asyncio
import os
import threading
from pathlib import Path
from dotenv import load_dotenv

from src.client import OpenLeADRClient
from src.live_charting import LiveCharting, DataGenerator
from src.openleadr_node.config.config import Container, Config
from src.openleadr_node.dependencies.venInterface import VenDependencyInterface
from src.openleadr_node.dependencies.ven_dependency import VenDependency
from src.server import OpenLeADRServer

current_path = Path.cwd()
shutdown_event = threading.Event()


def get_leadr_server(config: Config):
  return OpenLeADRServer(os.getenv('SERVER_NAME'), os.getenv('DB_NAME'), config)


def get_leadr_client(config: Config, controller: VenDependencyInterface):
  return OpenLeADRClient(os.getenv('VEN_NAME'), os.getenv('VTN_URL'), controller)


def get_dash_app(config: Config):
  return LiveCharting(os.getenv('DB_NAME'), os.getenv('METERVALUES_BD_NAME'), config)


def get_data_generator():
  return DataGenerator('./src/database/dummy_data_db', 'dummy_data_table')


def run_dash_app(config: Config):
  dash = get_dash_app(config)
  dash.app.run_server(debug=True, use_reloader=False)


def main():
  load_dotenv()

  container = Container()
  config = container.config()
  client_controller = VenDependency()
  loop = asyncio.get_event_loop()
  loop.create_task(get_leadr_server(config).server.run())
  loop.create_task(get_leadr_client(config, client_controller).client.run())

  # Start the Dash app in a separate thread
  threading.Thread(target=run_dash_app, args=(config,), daemon=True).start()

  # Run your asyncio tasks here
  loop.run_forever()


if __name__ == '__main__':
  try:
    main()
  except KeyboardInterrupt:
    print('Shutting down...')
