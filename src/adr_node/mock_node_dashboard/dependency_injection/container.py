# src/di/container.py
from dependency_injector import containers, providers
import logging.config

from src.adr_node.mock_node_dashboard.core.services.consumption_service import (
  ConsumptionServiceImpl,
)
from src.adr_node.mock_node_dashboard.core.services.slider_service import (
  SliderServiceImpl,
)
from src.adr_node.mock_node_dashboard.persistence.repository.file_slider_repository import (
  FileSliderRepository,
)
from src.adr_node.mock_node_dashboard.ui.app import AsyncGradioApp


class Container(containers.DeclarativeContainer):
  # Configuration
  config = providers.Configuration()

  # Configure logging
  logging_config = {
    'version': 1,
    'formatters': {
      'default': {
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
      },
    },
    'handlers': {
      'console': {
        'class': 'logging.StreamHandler',
        'formatter': 'default',
        'level': 'INFO',
      },
      'file': {
        'class': 'logging.FileHandler',
        'formatter': 'default',
        'filename': 'app.log',
        'level': 'INFO',
      },
    },
    'root': {
      'level': 'INFO',
      'handlers': ['console', 'file'],
    },
  }

  logging = providers.Resource(logging.config.dictConfig, config=logging_config)

  slider_repository = providers.Singleton(
    FileSliderRepository, file_path=config.slider_file_path
  )

  # Services
  consumption_service = providers.Singleton(
    ConsumptionServiceImpl,
    base_url=config.api_base_url,
    update_interval=config.update_interval,
  )

  slider_service = providers.Singleton(
    SliderServiceImpl,
    slider_repository=slider_repository,
    num_sliders=config.num_sliders,
    timezone_offset=config.timezone_offset,
    minutes_interval=config.minutes_interval,
    default_value=config.default_slider_value,
  )

  # UI Components
  gradio_app = providers.Singleton(
    AsyncGradioApp,
    consumption_service=consumption_service,
    slider_service=slider_service,
    num_sliders=config.num_sliders,
    max_slider_value=config.max_slider_value,
  )

  @classmethod
  def init_app(cls, app_config):
    container = cls()
    container.config.from_dict(app_config.__dict__)
    container.init_resources()

    # Start background services
    consumption_service = container.consumption_service()
    consumption_service.start()

    return container
