import logging
import os
import sys

from dotenv import load_dotenv

from src.openadr_node.models.rest_config import RestApiConfig
from src.openadr_node.node_controller import NodeController


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

  rest_api_config = RestApiConfig(port=int(os.getenv('REST_API_PORT', 5000)))

  node_manager = NodeController(
    node_id=os.getenv('NODE_ID'),
    vtn_name=os.getenv('VTN_NAME', 'default_vtn'),
    openadr_http_port=int(os.getenv('VTN_PORT', 8080)),
    openadr_vtn_path_prefix=os.getenv('VTN_PATH_PREFIX', '/0/OpenADR2/Simple/2.0b'),
    ven_name=os.getenv('VEN_NAME', 'default_ven'),
    vtn_url=os.getenv('CONNECT_VTN_URL'),
    rest_api_config=rest_api_config,
  )

  try:
    node_manager.run_node()
  except KeyboardInterrupt:
    logging.info('Shutting down node...')
  except Exception as e:
    logging.error(f'Error running node: {e}')
    sys.exit(1)


if __name__ == '__main__':
  main()
