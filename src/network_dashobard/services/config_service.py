import json
from typing import List

from src.network_dashobard.config.container_config import ContainerConfig


class ConfigService:
  def __init__(self, config_path: str):
    self.config_path = config_path

  def get_configs(self) -> List[ContainerConfig]:
    with open(self.config_path) as f:
      config_data = json.load(f)
      return [ContainerConfig(**config) for config in config_data]
