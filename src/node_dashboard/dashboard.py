import os
from typing import List
import sys

import gradio as gr

from .data_manager import DataManager
from .helper import constants
from .plot_manager import PlotManager
from .interface_manager import InterfaceManager
from .helper.config import ContainerConfig, ConfigManager
from src.node_dashboard.helper.logger import logger


class GradioNodeDashboard:
  """
  Represents the Gradio Node Dashboard for monitoring container data.

  Attributes
  ----------
  config_manager : ConfigManager
      Manages loading and handling of container configurations.
  configs : List[ContainerConfig]
      List of container configurations.
  state : List[ContainerConfig]
      Current state of the dashboard.
  data_manager : DataManager
      Manages data fetching and buffering.
  plot_manager : PlotManager
      Manages plot creation and updates.
  interface_manager : InterfaceManager
      Manages the Gradio interface creation and updates.
  """

  def __init__(self, file_path: str = './env_variables.json') -> None:
    """
    Initializes the GradioNodeDashboard with configurations and managers.

    Parameters
    ----------
    file_path : str, optional
        Path to the configuration file (default is "./env_variables.json").
    """
    print('FILE PATH', os.path.abspath(file_path))
    self.config_manager = ConfigManager(file_path)
    self.configs = self.config_manager.configs
    self.state = self.configs.copy()

    if not self.configs:
      logger.error('No configurations loaded. Exiting application.')
      sys.exit(1)

    self.data_manager = DataManager(self.configs, constants.MAX_BUFFER_SIZE)
    self.plot_manager = PlotManager()
    self.interface_manager = InterfaceManager(self)

  def update_state(self, new_state: List[ContainerConfig], merge: bool = False) -> None:
    """
    Updates the current state with a new state, with an option to merge.

    Parameters
    ----------
    new_state : List[ContainerConfig]
        New state to be set.
    merge : bool
        Whether to merge the new state with the existing state (default is False).

    Returns
    -------
    None
    """
    if merge:
      existing_configs = {config.container_name: config for config in self.state}
      for config in new_state:
        existing_configs[config.container_name] = config
      self.state = list(existing_configs.values())
    else:
      self.state = new_state

  def set_state_to_single_config(
    self, config: ContainerConfig, keep_existing: bool = False
  ) -> None:
    """
    Sets the state to a single configuration, with an option to keep existing configs.

    Parameters
    ----------
    config : ContainerConfig
        Configuration to be set as the state.
    keep_existing : bool
        Whether to keep existing configurations in the state (default is False).

    Returns
    -------
    None
    """
    if keep_existing:
      self.state = [config] + [
        cfg for cfg in self.state if cfg.container_name != config.container_name
      ]
    else:
      self.state = [config]

  def add_all_to_state(self) -> None:
    """
    Adds all configurations to the current state.

    Returns
    -------
    None
    """
    self.state = self.configs.copy()

  def add_layer_to_state(self, layer: int) -> None:
    """
    Adds configurations of a specific layer to the current state.

    Parameters
    ----------
    layer : int
        Layer number to filter configurations by.

    Returns
    -------
    None
    """
    self.state = [config for config in self.configs if config.layer == layer]

  def get_unique_layers(self) -> List[int]:
    """
    Gets a list of unique layers from the configurations.

    Returns
    -------
    List[int]
        List of unique layer numbers.
    """
    return sorted({config.layer for config in self.configs})

  def create_interface(self) -> gr.Blocks:
    """
    Creates the Gradio interface for the dashboard.

    Returns
    -------
    gr.Blocks
        Gradio interface blocks.
    """
    return self.interface_manager.create_interface()
