import json
import logging
from dataclasses import dataclass
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ContainerConfig:
  vtn_name: str
  vtn_url: str
  vtn_path_prefix: str
  ven_name: str
  gradio_port: str
  gradio_server_name: str
  rest_api_port: str
  vtn_self_host: str
  layer: int
  container_name: str


def load_configs(file_path: str) -> List[ContainerConfig]:
  configs = []
  try:
    with open(file_path) as f:
      data = json.load(f)
      for container_name, values in data.items():
        config = {
          'vtn_name': values['VTN_NAME'],
          'vtn_url': values['VTN_URL'],
          'vtn_path_prefix': values['VTN_PATH_PREFIX'],
          'ven_name': values['VEN_NAME'],
          'gradio_port': values['GRADIO_PORT'],
          'gradio_server_name': values['GRADIO_SERVER_NAME'],
          'rest_api_port': values['REST_API_PORT'],
          'vtn_self_host': values['VTN_SELF_HOST'],
          'layer': int(values['LAYER']),
          'container_name': container_name,
        }
        configs.append(ContainerConfig(**config))
  except FileNotFoundError:
    logger.error(f'Config file not found: {file_path}')
  except json.JSONDecodeError as e:
    logger.error(f'Invalid JSON in config file: {e}')
  return configs
