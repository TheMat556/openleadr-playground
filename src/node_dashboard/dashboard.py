from typing import List
import logging
import sys

import gradio as gr

from .data_manager import DataManager
from .helper import constants
from .plot_manager import PlotManager
from .interface_manager import InterfaceManager
from .helper.config import ContainerConfig, ConfigManager

logger = logging.getLogger(__name__)


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
    self.config_manager = ConfigManager(file_path)
    self.configs = self.config_manager.configs
    self.state = self.configs.copy()

    if not self.configs:
      logger.error('No configurations loaded. Exiting application.')
      sys.exit(1)

    self.data_manager = DataManager(self.configs, constants.MAX_BUFFER_SIZE)
    self.plot_manager = PlotManager()
    self.interface_manager = InterfaceManager(self)

  def update_state(self, new_state: List[ContainerConfig]) -> None:
    """
    Updates the current state with a new state.

    Parameters
    ----------
    new_state : List[ContainerConfig]
        New state to be set.

    Returns
    -------
    None
    """
    self.state = new_state

  def set_state_to_single_config(self, config: ContainerConfig) -> None:
    """
    Sets the state to a single configuration.

    Parameters
    ----------
    config : ContainerConfig
        Configuration to be set as the state.

    Returns
    -------
    None
    """
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
