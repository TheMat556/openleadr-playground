import logging
import os
import signal
import sys
from contextlib import contextmanager
from multiprocessing import Process, Queue

from dotenv import load_dotenv

from development.simple.node_runner import (
  run_mock_node,
  run_house_node,
  run_node_dashboard,
)


@contextmanager
def manage_processes(processes_list):
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


def signal_handler(signum, frame):
  logging.info('Received shutdown signal, terminating processes...')
  sys.exit(0)


if __name__ == '__main__':
  load_dotenv(dotenv_path='./development_configs/simple/.env')
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
        message = queue.get()
        if message == 'vtn_created':
          house_node_0_process = Process(
            target=run_house_node,
            kwargs={
              'ven_name': os.getenv('DEV_VEN_NAME_0'),
              'vtn_url': os.getenv('DEV_VTN_URL'),
              'rest_api_port': os.getenv('DEV_HOUSE_NODE_0_REST_API'),
            },
          )
          house_node_0_process.start()

          house_node_1_process = Process(
            target=run_house_node,
            kwargs={
              'ven_name': os.getenv('DEV_VEN_NAME_1'),
              'vtn_url': os.getenv('DEV_VTN_URL'),
              'rest_api_port': os.getenv('DEV_HOUSE_NODE_1_REST_API'),
            },
          )
          house_node_1_process.start()
    except KeyboardInterrupt:
      pass
