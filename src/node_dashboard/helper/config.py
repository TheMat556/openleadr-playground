# src/node_dashboard/config_manager.py
import json
import logging
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

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


class ConfigManager:
  """
  Manages loading and validation of container configurations.
  """

  REQUIRED_KEYS = [
    'VTN_NAME',
    'VTN_URL',
    'VTN_PATH_PREFIX',
    'VEN_NAME',
    'GRADIO_PORT',
    'GRADIO_SERVER_NAME',
    'REST_API_PORT',
    'VTN_SELF_HOST',
    'LAYER',
  ]

  def __init__(self, file_path: str):
    """
    Initialize the ConfigManager with a configuration file path.

    Args:
        file_path (str): Path to the JSON configuration file
    """
    self.file_path = file_path
    self.configs: List[ContainerConfig] = self._load_configs()

  def _load_configs(self) -> List[ContainerConfig]:
    """
    Load configurations from the JSON file.

    Returns:
        List[ContainerConfig]: List of validated container configurations
    """
    try:
      with open(self.file_path) as f:
        data = json.load(f)
      return self._parse_configs(data)
    except FileNotFoundError:
      logger.error(f'Config file not found: {self.file_path}')
      return []
    except json.JSONDecodeError as e:
      logger.error(f'Invalid JSON in config file: {e}')
      return []

  def _parse_configs(self, data: Dict[str, Any]) -> List[ContainerConfig]:
    """
    Parse and validate the configuration data.

    Args:
        data (Dict[str, Any]): Raw configuration data from JSON

    Returns:
        List[ContainerConfig]: List of validated container configurations
    """
    configs = []
    for container_name, values in data.items():
      config = self._validate_and_create_config(container_name, values)
      if config:
        configs.append(config)
    return configs

  def _validate_and_create_config(
    self, container_name: str, values: Dict[str, Any]
  ) -> Optional[ContainerConfig]:
    """
    Validate configuration values and create a ContainerConfig instance.

    Args:
        container_name (str): Name of the container
        values (Dict[str, Any]): Configuration values for the container

    Returns:
        Optional[ContainerConfig]: Validated ContainerConfig instance or None if validation fails
    """
    # Validate required keys
    if missing_keys := self._get_missing_keys(values):
      logger.error(
        f"Missing keys {missing_keys} in config for container '{container_name}'"
      )
      return None

    try:
      config_dict = {
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
      return ContainerConfig(**config_dict)
    except ValueError as e:
      logger.error(f"Error creating config for container '{container_name}': {e}")
      return None

  def _get_missing_keys(self, values: Dict[str, Any]) -> List[str]:
    """
    Get a list of missing required keys from the configuration values.

    Args:
        values (Dict[str, Any]): Configuration values to check

    Returns:
        List[str]: List of missing required keys
    """
    return [key for key in self.REQUIRED_KEYS if key not in values]

  def get_config_by_name(self, container_name: str) -> Optional[ContainerConfig]:
    """
    Get a container configuration by container name.

    Args:
        container_name (str): Name of the container

    Returns:
        Optional[ContainerConfig]: Container configuration if found, None otherwise
    """
    for config in self.configs:
      if config.container_name == container_name:
        return config
    return None

  def get_configs_by_layer(self, layer: int) -> List[ContainerConfig]:
    """
    Get all container configurations for a specific layer.

    Args:
        layer (int): Layer number

    Returns:
        List[ContainerConfig]: List of container configurations in the specified layer
    """
    return [config for config in self.configs if config.layer == layer]
