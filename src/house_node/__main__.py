import os
import sys
from datetime import timedelta

import numpy as np
from dotenv import load_dotenv

from src.openadr_node.models import ReportConfiguration
from src.openadr_node.node_manager import NodeManager


rng = np.random.default_rng()

def sample_callback_1():
    print('callback 1')
    return rng.random() * 10

def sample_callback_2():
    print('callback 2')
    return rng.random() * 10


def main():
  load_dotenv()
  reports = [
    ReportConfiguration(
      resource_id='res_123',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=sample_callback_1,
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
    ReportConfiguration(
      resource_id='res_456',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=sample_callback_2,
      additional_metadata={'unit': '%', 'location': 'Room 202'},
    ),
  ]

  node_manager = NodeManager(
    ven_name=os.getenv('VEN_NAME'),
    vtn_url=os.getenv('CONNECT_VTN_URL'),
    rest_api_port=os.getenv('REST_API_PORT'),
  )
  node_manager.add_report(reports)
  try:
    node_manager.run_node()
  except KeyboardInterrupt:
    sys.exit(0)


if __name__ == '__main__':
  main()
