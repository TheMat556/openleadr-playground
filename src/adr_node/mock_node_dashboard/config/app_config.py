# src/config/app_config.py
from dataclasses import dataclass


@dataclass
class EnergyControlPanelConfig:
  slider_file_path: str
  num_sliders: int = 24
  timezone_offset: int = 1  # UTC+1
  update_interval: int = 5  # seconds
  minutes_interval: int = 15
  max_slider_value: int = 30
  default_slider_value: int = 30
