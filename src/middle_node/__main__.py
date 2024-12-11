import logging
import os
import sys
from datetime import timedelta

import numpy as np
from dotenv import load_dotenv

from src.openadr_node.models import ReportConfiguration
from src.openadr_node.node_manager import NodeManager


def sample_callback_1():
  print('callback 1')
  return np.random.rand() * 10


def main():
  load_dotenv()
  # It seems the VEN needs at least 1 report to be able to work properly
  reports = [
    ReportConfiguration(
      resource_id='res_123',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=sample_callback_1,
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
  ]

  node_manager = NodeManager(
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    http_port=os.getenv('VTN_PORT', 8080),  # http_port=8081,
    vtn_path_prefix=os.getenv(
      'VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'
    ),  # /0/0/OpenADR2/Simple/2.0b', #
    ven_name=os.getenv('VEN_NAME', 'default_ven'),
    vtn_url=os.getenv(
      'CONNECT_VTN_URL'
    ),  #'http://127.0.0.1:8080/0/OpenADR2/Simple/2.0b'
  )

  try:
    node_manager.add_report(reports)
    node_manager.run_node()
  except KeyboardInterrupt:
    logging.info('Shutting down node...')
  except Exception as e:
    logging.error(f'Error running node: {e}')
    sys.exit(0)


if __name__ == '__main__':
  main()
