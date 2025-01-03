import logging
import os
import signal
import sys
from contextlib import contextmanager
from multiprocessing import Process, Queue
from queue import Empty
from typing import List, Generator

from dotenv import load_dotenv

from development.simple.node_runner import (
  run_mock_node,
  run_house_node,
  run_node_dashboard,
)


@contextmanager
def manage_processes(
  processes_list: List[Process],
) -> Generator[List[Process], None, None]:
  try:
    for p in processes_list:
      p.start()
    yield processes_list
  except Exception as e:
    logging.error(f'Error managing processes: {e}')
    raise
  finally:
    for p in processes_list:
      if p.is_alive():
        p.terminate()
        p.join(timeout=5)
        if p.is_alive():
          p.kill()


def signal_handler(signum: int, frame: None) -> None:
  logging.info('Received shutdown signal, terminating processes...')
  sys.exit(0)


if __name__ == '__main__':
  logging.basicConfig(
    level=os.getenv('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
  )
  load_dotenv(dotenv_path='./development/simple/.env')
  load_dotenv(dotenv_path='./development/simple/.env.mqtt')

  signal.signal(signal.SIGTERM, signal_handler)
  signal.signal(signal.SIGINT, signal_handler)

  queue = Queue()

  processes = [
    Process(target=run_mock_node, args=(queue,)),
    Process(target=run_node_dashboard),
  ]

  with manage_processes(processes):
    try:
      while True:
        try:
          message = queue.get(timeout=1)
        except Empty:
          continue
        if message == 'vtn_created':
          house_node_0_process = Process(
            target=run_house_node,
            kwargs={
              'node_id': os.getenv('DEV_NODE_ID_0_0'),
              'ven_name': os.getenv('DEV_VEN_NAME_0'),
              'vtn_url': os.getenv('DEV_VTN_URL'),
              'rest_api_port': os.getenv('DEV_HOUSE_NODE_0_REST_API'),
              'mqtt_broker': os.getenv('PRIVATE_MQTT_BROKER_URL'),
              'mqtt_port': int(os.getenv('PRIVATE_MQTT_PORT')),
              'mqtt_topic_load_profile': os.getenv('PRIVATE_MQTT_TOPIC_LOAD_PROFILE'),
              'mqtt_topic_consumption': os.getenv(
                'PRIVATE_MQTT_TOPIC_LOAD_CONSUMPTION'
              ),
              'mqtt_username': os.getenv('PRIVATE_MQTT_USERNAME'),
              'mqtt_password': os.getenv('PRIVATE_MQTT_PASSWORD'),
            },
          )
          house_node_0_process.start()
          processes.append(house_node_0_process)

          house_node_1_process = Process(
            target=run_house_node,
            kwargs={
              'node_id': os.getenv('DEV_NODE_ID_0_1'),
              'ven_name': os.getenv('DEV_VEN_NAME_1'),
              'vtn_url': os.getenv('DEV_VTN_URL'),
              'rest_api_port': os.getenv('DEV_HOUSE_NODE_1_REST_API'),
            },
          )
          house_node_1_process.start()
          processes.append(house_node_1_process)
    except KeyboardInterrupt:
      logging.info('Shutting down due to KeyboardInterrupt')
      sys.exit(0)
