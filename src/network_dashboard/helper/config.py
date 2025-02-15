import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import jsonschema
from cachetools.func import lru_cache
import logging


@dataclass
class ContainerConfig:
  """Configuration for a container instance."""

  node_id: str
  vtn_name: str
  vtn_url: str
  vtn_path_prefix: str
  ven_name: str
  gradio_port: int
  gradio_server_name: str
  rest_api_port: int
  rest_api_host: str
  vtn_self_host: str
  layer: int
  container_name: str


class ConfigManager:
  """Manages loading and validation of container configurations."""

  REQUIRED_KEYS: frozenset[str] = frozenset(
    {
      'OPENADR_NODE_ID',
      'OPENADR_VTN_IDENTIFIER',
      'OPENADR_VTN_ENDPOINT_URL',
      'OPENADR_VTN_PATH_PREFIX',
      'OPENADR_VEN_IDENTIFIER',
      'UI_GRADIO_PORT',
      'UI_GRADIO_HOST',
      'API_REST_PORT',
      'API_REST_HOST',
      'OPENADR_VTN_PORT',
      'OPENADR_VTN_HOST',
      'OPENADR_LAYER_ID',
    }
  )

  MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

  JSON_SCHEMA = {
    'type': 'object',
    'patternProperties': {
      '^[a-zA-Z0-9_-]+$': {
        'type': 'object',
        'required': list(REQUIRED_KEYS),
        'properties': {
          'OPENADR_NODE_ID': {'type': 'string'},
          'OPENADR_VTN_IDENTIFIER': {'type': 'string'},
          'OPENADR_VTN_ENDPOINT_URL': {'type': 'string'},
          'OPENADR_VTN_PATH_PREFIX': {'type': 'string'},
          'OPENADR_VEN_IDENTIFIER': {'type': 'string'},
          'UI_GRADIO_PORT': {'type': ['string', 'integer']},
          'UI_GRADIO_HOST': {'type': 'string'},
          'API_REST_PORT': {'type': ['string', 'integer']},
          'API_REST_HOST': {'type': 'string'},
          'OPENADR_VTN_PORT': {'type': ['string', 'integer']},
          'OPENADR_VTN_HOST': {'type': 'string'},
          'OPENADR_LAYER_ID': {'type': ['string', 'integer']},
          'OPENADR_VTN_CONNECT_URL': {'type': 'string'},
        },
      }
    },
  }

  def __init__(self, file_path: str):
    """
    Initialize the ConfigManager with a configuration file path.

    Args:
        file_path (str): Path to the JSON configuration file
    Raises:
        FileNotFoundError: If the configuration file is not found
        json.JSONDecodeError: If the configuration file contains invalid JSON
        ValueError: If the configuration file contains invalid data
    """
    self.file_path = Path(file_path).resolve()
    if not self.file_path.is_file():
      raise FileNotFoundError(f'Config file not found: {self.file_path}')
    if self.file_path.stat().st_size > self.MAX_FILE_SIZE:
      raise ValueError(f'Config file is too large: {self.file_path}')

    self.configs: List[ContainerConfig] = self._load_configs()
    if not self.configs:
      raise ValueError(f'Failed to load valid configurations from {self.file_path}')

  def _load_configs(self) -> List[ContainerConfig]:
    """
    Load configurations from the JSON file.

    Returns:
        List[ContainerConfig]: List of validated container configurations
    """
    try:
      logging.info('Attempting to read the configuration file.')
      with self.file_path.open() as f:
        data = json.load(f)
      logging.info(f'Successfully loaded configuration from {self.file_path}')

      try:
        jsonschema.validate(data, self.JSON_SCHEMA)
      except jsonschema.exceptions.ValidationError as e:
        logging.error(f'Schema validation failed: {e}')
        raise ValueError(f'Schema validation failed: {e.message}')

      return self._parse_configs(data)
    except json.JSONDecodeError as e:
      logging.error(f'Invalid JSON in config file: {e}')
      raise ValueError(f'Invalid JSON in config file: {e.msg}')

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
    if missing_keys := self._get_missing_keys(values):
      logging.error(
        f"Missing keys {missing_keys} in config for container '{container_name}'"
      )
      return None

    def validate_port(port: Any) -> bool:
      if not port:
        return True
      try:
        return 1024 <= int(port) <= 65535
      except ValueError:
        return False

    try:
      layer = int(values['OPENADR_LAYER_ID'])
      if layer < 0:
        raise ValueError(f'Invalid layer value: {layer}')
      gradio_port = values['UI_GRADIO_PORT']
      rest_api_port = values['API_REST_PORT']
      if not validate_port(gradio_port):
        raise ValueError(f'Invalid Gradio port: {gradio_port}')
      if not validate_port(rest_api_port):
        raise ValueError(f'Invalid REST API port: {rest_api_port}')  #
      config_dict = {
        'node_id': values['OPENADR_NODE_ID'],
        'vtn_name': values['OPENADR_VTN_IDENTIFIER'],
        'vtn_url': values['OPENADR_VTN_ENDPOINT_URL'],
        'vtn_path_prefix': values['OPENADR_VTN_PATH_PREFIX'],
        'ven_name': values['OPENADR_VEN_IDENTIFIER'],
        'gradio_port': int(gradio_port),
        'gradio_server_name': values['UI_GRADIO_HOST'],
        'rest_api_port': int(rest_api_port),
        'rest_api_host': values['API_REST_HOST'],
        'vtn_self_host': values['OPENADR_VTN_HOST'],
        'layer': layer,
        'container_name': container_name,
      }
      return ContainerConfig(**config_dict)
    except ValueError as e:
      logging.error(f"Error creating config for container '{container_name}': {e}")
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

  @lru_cache(maxsize=None)
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

  @lru_cache(maxsize=None)
  def get_configs_by_layer(self, layer: int) -> List[ContainerConfig]:
    """
    Get all container configurations for a specific layer.

    Args:
        layer (int): Layer number

    Returns:
        List[ContainerConfig]: List of container configurations in the specified layer
    """
    return [config for config in self.configs if config.layer == layer]
