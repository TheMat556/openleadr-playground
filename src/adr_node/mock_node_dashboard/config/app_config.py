from dataclasses import dataclass


@dataclass
class EnergyControlPanelConfig:
  """
  Configuration for the Energy Control Panel.

  :param slider_file_path: Path to the slider configuration file.
  :type slider_file_path: str
  :param num_sliders: Number of sliders in the control panel.
  :type num_sliders: int
  :param timezone_offset: Timezone offset from UTC.
  :type timezone_offset: int
  :param update_interval: Interval in seconds for updating the control panel.
  :type update_interval: int
  :param minutes_interval: Interval in minutes for slider adjustments.
  :type minutes_interval: int
  :param max_slider_value: Maximum value for the sliders.
  :type max_slider_value: int
  :param default_slider_value: Default value for the sliders.
  :type default_slider_value: int
  """

  slider_file_path: str
  num_sliders: int = 24
  timezone_offset: int = 1  # UTC+1
  update_interval: int = 5  # seconds
  minutes_interval: int = 15
  max_slider_value: int = 30
  default_slider_value: int = 30
