import logging
import os
import sys
from datetime import timedelta
from typing import List, Optional

import numpy as np
from dotenv import load_dotenv

from src.openadr_node.models import ReportConfiguration
from src.openadr_node.node_manager import NodeManager


def generate_measurement(
  measurement_type: str, min_value: float = 0, max_value: float = 10
) -> float:
  """Generate a random measurement value within specified bounds."""
  logging.info(f'Generating {measurement_type} measurement')
  measurement = np.random.rand() * (max_value - min_value) + min_value
  logging.debug(f'Generated measurement: {measurement}')
  return measurement


def validate_config() -> None:
  required_vars = [
    'VTN_NAME',
    'VTN_PORT',
    'VTN_PATH_PREFIX',
    'VEN_NAME',
    'CONNECT_VTN_URL',
  ]
  missing_vars = [var for var in required_vars if not os.getenv(var)]
  if missing_vars:
    raise ValueError(
      f"Missing required environment variables: {', '.join(missing_vars)}"
    )


def main() -> None:
  load_dotenv()
  validate_config()
  # It seems the VEN needs at least 1 report to be able to work properly
  reports: List[ReportConfiguration] = [
    ReportConfiguration(
      resource_id='res_123',
      measurement='energy',
      sampling_rate=timedelta(seconds=5),
      callback=lambda: generate_measurement('energy'),
      additional_metadata={'unit': 'Celsius', 'location': 'Room 101'},
    ),
  ]

  node_manager = NodeManager(
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    http_port=int(os.getenv('VTN_PORT', 8080)),
    vtn_path_prefix=os.getenv('VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'),
    ven_name=os.getenv('VEN_NAME', 'default_ven'),
    vtn_url=os.getenv('CONNECT_VTN_URL'),
  )

  try:
    node_manager.add_report(reports)
    node_manager.run_node()
  except KeyboardInterrupt:
    logging.info('Shutting down node...')
  except Exception as e:
    logging.error(f'Error running node: {e}')
    sys.exit(1)


if __name__ == '__main__':
  main()
