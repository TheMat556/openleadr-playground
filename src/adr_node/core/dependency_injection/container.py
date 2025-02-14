from dependency_injector import containers, providers
from openleadr import OpenADRClient, OpenADRServer

from src.adr_node.communication.rest.services.rest_service import RestService
from src.adr_node.config.application_config import ApplicationConfig
from src.adr_node.core.nodes.configs.virtual_end_node_config import VirtualEndNodeConfig
from src.adr_node.core.nodes.configs.virtual_top_node_config import VirtualTopNodeConfig
from src.adr_node.core.nodes.implementation.virtual_end_node import VirtualEndNode
from src.adr_node.core.nodes.implementation.virtual_top_node import VirtualTopNode
from src.adr_node.core.services.adr.adr_service import AdrService
from src.adr_node.core.controller.node_component_controller import (
  NodeComponentController,
)
from src.adr_node.core.services.distribution_v2.calculators.resource_calculator import (
  ResourceCalculator,
)
from src.adr_node.core.services.distribution_v2.domain.distribution_parameters import (
  DistributionParameters,
)
from src.adr_node.core.services.distribution_v2.generators.profile_generator import (
  ProfileGenerator,
)
from src.adr_node.core.services.distribution_v2.generators.time_interval import (
  TimeIntervalGenerator,
)
from src.adr_node.core.services.distribution_v2.services.distribution_service import (
  DistributionService,
)
from src.adr_node.database.repositories.sqlite_consumption_repository import (
  SQLiteConsumptionRepository,
)
from src.adr_node.database.repositories.sqlite_load_profile_repository import (
  SQLiteLoadProfileRepository,
)
from src.adr_node.database.repositories.sqlite_z_value_repository import (
  SQLiteZValueRepository,
)
from src.adr_node.database.services.core.consumption_service import ConsumptionService
from src.adr_node.database.services.base.database_service import SQLiteDatabaseService
from src.adr_node.database.services.core.load_profile_service import LoadProfileService
from src.adr_node.database.services.core.z_value_service import ZValueService
from src.adr_node.event_bus.implementation.pydispatch_event_bus import (
  PyDispatchEventBus,
)
from src.adr_node.mock_node_dashboard.core.services.slider_service import SliderService
from src.adr_node.mock_node_dashboard.persistence.repository.file_slider_repository import (
  FileSliderRepository,
)
from src.adr_node.mock_node_dashboard.ui.app import EnergyControlPanel


class Container(containers.DeclarativeContainer):
  wiring_config = containers.WiringConfiguration(modules=['__main__'])

  config = providers.Configuration()

  # Database / Services (Tier 1)
  database_service = providers.Singleton(
    SQLiteDatabaseService,
    db_path=providers.Callable(
      lambda node_id: f'data/{node_id}.db',
      node_id=config.adr_config.node_id,
    ),
  )

  resource_calculator = providers.Singleton(ResourceCalculator)
  time_interval_generator = providers.Singleton(TimeIntervalGenerator)
  profile_generator = providers.Singleton(ProfileGenerator)
  distribution_params = providers.Singleton(
    DistributionParameters,
    time_window_ms=config.distribution_config.time_window_ms,
    max_g_value=config.distribution_config.max_g_value,
    correction_factor_a=config.distribution_config.correction_factor_a,
    correction_factor_b=config.distribution_config.correction_factor_b,
    correction_factor_c=config.distribution_config.correction_factor_c,
  )

  load_profile_repository = providers.Singleton(
    SQLiteLoadProfileRepository, db_service=database_service
  )

  consumption_repository = providers.Singleton(
    SQLiteConsumptionRepository, db_service=database_service
  )

  z_value_repository = providers.Singleton(
    SQLiteZValueRepository, db_service=database_service
  )

  load_profile_service = providers.Singleton(
    LoadProfileService, repository=load_profile_repository
  )

  consumption_service = providers.Singleton(
    ConsumptionService, repository=consumption_repository
  )

  z_value_service = providers.Singleton(ZValueService, repository=z_value_repository)

  event_bus = providers.Singleton(PyDispatchEventBus)

  # Components (Tier 2)
  openadr_client_factory = providers.Factory(OpenADRClient)

  virtual_end_node_config = providers.Factory(
    VirtualEndNodeConfig,
    ven_name=config.adr_config.ven_name,
    vtn_url=config.adr_config.vtn_url,
  )

  virtual_end_node = providers.Singleton(
    lambda config, load_profile_service, consumption_service, event_bus: VirtualEndNode(
      config, load_profile_service, consumption_service, event_bus
    )
    if config and config.ven_name and config.vtn_url
    else None,
    load_profile_service=load_profile_service,
    consumption_service=consumption_service,
    config=virtual_end_node_config.provided,
    event_bus=event_bus,
  )

  openadr_server_factory = providers.Factory(OpenADRServer)

  virtual_top_node_config = providers.Factory(
    VirtualTopNodeConfig,
    vtn_id=config.adr_config.vtn_name,
    http_port=config.adr_config.openadr_http_port,
    http_host=config.adr_config.openadr_http_host,
    path_prefix=config.adr_config.openadr_vtn_path_prefix,
  )

  virtual_top_node = providers.Singleton(
    lambda config,
    sqlite_consumption_service,
    load_profile_service,
    z_value_service,
    event_bus: VirtualTopNode(
      config=config,
      sqlite_consumption_service=sqlite_consumption_service,
      load_profile_service=load_profile_service,
      z_value_service=z_value_service,
      event_bus=event_bus,
    )
    if config and config.http_host and config.http_port and config.path_prefix
    else None,
    config=virtual_top_node_config.provided,
    sqlite_consumption_service=consumption_service,
    load_profile_service=load_profile_service,
    z_value_service=z_value_service,
    event_bus=event_bus,
  )

  rest_service = providers.Singleton(
    RestService,
    host=config.rest_config.host,
    port=config.rest_config.port,
    load_profile_service=load_profile_service,
    consumption_service=consumption_service,
  )

  adr_service = providers.Singleton(
    AdrService,
    adr_config=config.adr_config,
    virtual_end_node=virtual_end_node,
    virtual_top_node=virtual_top_node,
  )

  slider_repository = providers.Singleton(
    FileSliderRepository,
    file_path=config.slider_file_path,
    load_profile_service=load_profile_service.provided,
  )

  slider_service = providers.Singleton(
    SliderService,
    slider_repository=slider_repository,
    event_bus=event_bus,
  )

  energy_control_panel = providers.Singleton(
    EnergyControlPanel,
    consumption_service=consumption_service,
    loadprofile_service=load_profile_service,
    slider_service=slider_service,
    num_sliders=config.energy_control_panel_config.num_sliders,
    max_slider_value=config.energy_control_panel_config.max_slider_value,
    update_interval=config.energy_control_panel_config.update_interval,
  )

  # Distribution service
  distribution_service = providers.Singleton(
    DistributionService,
    resource_calculator=resource_calculator,
    time_interval_generator=time_interval_generator,
    profile_generator=profile_generator,
    consumption_service=consumption_service,
    load_profile_service=load_profile_service,
    z_value_service=z_value_service,
    parameters=distribution_params,
    event_bus=event_bus,
  )

  @classmethod
  def create(cls, application_config: ApplicationConfig):
    container = cls()
    container.config.adr_config.from_dict(application_config.adr_config.__dict__)
    if application_config.mqtt_config is not None:
      container.config.mqtt_config.from_dict(application_config.mqtt_config.__dict__)
    if application_config.rest_config is not None:
      container.config.rest_config.from_dict(application_config.rest_config.__dict__)
    if application_config.energy_control_panel_config is not None:
      container.config.energy_control_panel_config.from_dict(
        application_config.energy_control_panel_config.__dict__
      )

    # Initialize resources (logging, etc.)
    # container.init_resources()

    # Create the list of runnable services
    runnable_services = [
      container.adr_service(),
      container.rest_service(),
    ]

    if application_config.adr_config.vtn_name:
      runnable_services.append(container.distribution_service())

    if (
      application_config.energy_control_panel_config is not None
      and application_config.energy_control_panel_config.num_sliders
    ):
      runnable_services.append(container.energy_control_panel())

    container.node_component_controller = NodeComponentController(
      runnable_services=runnable_services
    )

    return container, container.node_component_controller
