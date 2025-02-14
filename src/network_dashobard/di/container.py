from dependency_injector import containers, providers

from ..implementations.data_manager import DataManager
from ..implementations.interface_manager import InterfaceManager
from ..implementations.plot_manager import PlotManager
from ..services.http_client import HttpClient
from ..services.plot_service import PlotService
from ..services.time_service import TimeService
from ..services.uiservice import UIService
from ..services.update_service import UpdateService


class Container(containers.DeclarativeContainer):
  config = providers.Configuration()

  # Services
  http_client = providers.Singleton(HttpClient)
  time_service = providers.Singleton(TimeService)
  plot_service = providers.Singleton(PlotService)
  ui_service = providers.Singleton(UIService)
  update_service = providers.Singleton(UpdateService)

  # Managers
  data_manager = providers.Singleton(
    DataManager,
    http_client=http_client,
    time_service=time_service,
    configs=config.configs,
    max_buffer_size=config.max_buffer_size,
  )

  plot_manager = providers.Singleton(
    PlotManager, plot_service=plot_service, time_service=time_service
  )

  interface_manager = providers.Singleton(
    InterfaceManager,
    ui_service=ui_service,
    update_service=update_service,
    plot_manager=plot_manager,
    data_manager=data_manager,
  )
