from typing import List
import gradio as gr
from dependency_injector.wiring import inject, Provide

from src.network_dashobard.config.container_config import ContainerConfig
from src.network_dashobard.di.container import Container
from src.network_dashobard.interfaces.idata_manager import IDataManager
from src.network_dashobard.interfaces.iinterface_manager import IInterfaceManager
from src.network_dashobard.interfaces.iplot_manager import IPlotManager
from src.network_dashobard.services.config_service import ConfigService
from src.network_dashobard.services.update_service import UpdateService


class GradioNodeDashboard:
  @inject
  def __init__(
    self,
    config_service: ConfigService = Provide[Container.config_service],
    data_manager: IDataManager = Provide[Container.data_manager],
    plot_manager: IPlotManager = Provide[Container.plot_manager],
    interface_manager: IInterfaceManager = Provide[Container.interface_manager],
    update_service: UpdateService = Provide[Container.update_service],
  ):
    self.config_service = config_service
    self.data_manager = data_manager
    self.plot_manager = plot_manager
    self.interface_manager = interface_manager
    self.update_service = update_service

    self.configs = self.config_service.get_configs()
    self.state = self.configs.copy()

  def create_interface(self) -> gr.Blocks:
    return self.interface_manager.create_interface()

  def update_state(self, new_state: List[ContainerConfig], merge: bool = False) -> None:
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
    if keep_existing:
      self.state = [config] + [
        cfg for cfg in self.state if cfg.container_name != config.container_name
      ]
    else:
      self.state = [config]

  def add_all_to_state(self) -> None:
    self.state = self.configs.copy()

  def add_layer_to_state(self, layer: int) -> None:
    self.state = [config for config in self.configs if config.layer == layer]

  def get_unique_layers(self) -> List[int]:
    return sorted({config.layer for config in self.configs})
