from dataclasses import dataclass
from typing import List
import json
from pathlib import Path

from .container_config import ContainerConfig
from ..helper.constants import Environment, MAX_BUFFER_SIZE, UPDATE_INTERVAL


@dataclass
class AppConfig:
  node_configs: List[ContainerConfig]
  max_buffer_size: int = MAX_BUFFER_SIZE
  update_interval: float = UPDATE_INTERVAL
  environment: str = Environment.DOCKER

  @classmethod
  def from_file(cls, config_path: str) -> 'AppConfig':
    """Creates an AppConfig instance from a JSON configuration file"""
    config_path = Path(config_path)
    if not config_path.exists():
      raise FileNotFoundError(f'Configuration file not found: {config_path}')

    with config_path.open() as f:
      config_data = json.load(f)

    return cls(
      node_configs=[
        ContainerConfig(**node_config)
        for node_config in config_data.get('node_configs', [])
      ],
      max_buffer_size=config_data.get('max_buffer_size', MAX_BUFFER_SIZE),
      update_interval=config_data.get('update_interval', UPDATE_INTERVAL),
      environment=config_data.get('environment', Environment.DOCKER),
    )
