from typing import Dict, List
import gradio as gr

from src.network_dashobard.config.container_config import ContainerConfig
from src.network_dashobard.interfaces.idata_manager import IDataManager
from src.network_dashobard.interfaces.iinterface_manager import IInterfaceManager
from src.network_dashobard.interfaces.iplot_manager import IPlotManager
from src.network_dashobard.services.services import IUpdateService, IUIService


class InterfaceManager(IInterfaceManager):
  def __init__(
    self,
    ui_service: IUIService,
    update_service: IUpdateService,
    plot_manager: IPlotManager,
    data_manager: IDataManager,
  ):
    self.ui_service = ui_service
    self.update_service = update_service
    self.plot_manager = plot_manager
    self.data_manager = data_manager
    self._plot_components: Dict[str, gr.Plot] = {'hierarchy': gr.Plot(visible=False)}

  def create_interface(self) -> gr.Blocks:
    """Creates the Gradio interface"""
    with gr.Blocks(css=self.ui_service.get_css_styles()) as interface:
      self._create_layout()
      self._setup_update_callbacks()
      return interface

  def _create_layout(self) -> None:
    """Creates the interface layout"""
    with gr.Row(elem_id='dashboard-layout'):
      self._create_sidebar()
      self._create_main_content()

  def _create_sidebar(self) -> None:
    """Creates the sidebar components"""
    with gr.Column(elem_id='sidebar', scale=1):
      self.ui_service.create_sidebar_components(self._plot_components)

  def _create_main_content(self) -> None:
    """Creates the main content area"""
    with gr.Column(elem_id='main-content', scale=4):
      self.ui_service.create_main_content(self._plot_components)

  def _setup_update_callbacks(self) -> None:
    """Sets up data update callbacks"""
    self.update_service.setup_callbacks(self._plot_components)

  def _update_plots(self, state: List[ContainerConfig]) -> List[gr.Plot]:
    """Updates plot components based on state"""
    return self.ui_service.update_plots(state, self._plot_components)
