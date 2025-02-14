from abc import ABC, abstractmethod
import gradio as gr
from typing import List

from src.network_dashobard.config.container_config import ContainerConfig


class IInterfaceManager(ABC):
  @abstractmethod
  def create_interface(self) -> gr.Blocks:
    pass

  @abstractmethod
  def _update_plots(self, state: List[ContainerConfig]) -> List[gr.Plot]:
    pass
