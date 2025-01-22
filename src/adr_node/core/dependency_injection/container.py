from dependency_injector import containers, providers
from openleadr import OpenADRClient, OpenADRServer

from src.adr_node.communication.rest.services.rest_service import RestService
from src.adr_node.core.nodes.configs.virtual_end_node_config import VirtualEndNodeConfig
from src.adr_node.core.nodes.configs.virtual_top_node_config import VirtualTopNodeConfig
from src.adr_node.core.nodes.implementation.virtual_end_node import VirtualEndNode
from src.adr_node.core.nodes.implementation.virtual_top_node import VirtualTopNode
from src.adr_node.core.services.adr.adr_service import AdrService
from src.adr_node.core.controller.node_component_controller import (
  NodeComponentController,
)
from src.adr_node.config.application_config import ApplicationConfig
from src.adr_node.database.repositories.sqlite_consumption_repository import (
  SQLiteConsumptionRepository,
)
from src.adr_node.database.repositories.sqlite_load_profile_repository import (
  SQLiteLoadProfileRepository,
)
from src.adr_node.database.services.consumption_service import ConsumptionService
from src.adr_node.database.services.database_service import SQLiteDatabaseService
from src.adr_node.database.services.load_profile_service import LoadProfileService


class Container(containers.DeclarativeContainer):
  wiring_config = containers.WiringConfiguration(modules=['__main__'])

  config = providers.Configuration()

  # Database / Services (Tier 1)
  database_service = providers.Singleton(
    SQLiteDatabaseService, db_path='data/adr_node.db'
  )

  load_profile_repository = providers.Singleton(
    SQLiteLoadProfileRepository, db_service=database_service
  )

  consumption_repository = providers.Singleton(
    SQLiteConsumptionRepository, db_service=database_service
  )

  load_profile_service = providers.Singleton(
    LoadProfileService, repository=load_profile_repository
  )

  consumption_service = providers.Singleton(
    ConsumptionService, repository=consumption_repository
  )

  # Components (Tier 2)
  openadr_client_factory = providers.Factory(OpenADRClient)

  virtual_end_node_config = providers.Factory(
    VirtualEndNodeConfig,
    ven_name=config.adr_config.ven_name,
    vtn_url=config.adr_config.vtn_url,
  )

  virtual_end_node = providers.Singleton(
    lambda config: VirtualEndNode(config)
    if config and config.ven_name and config.vtn_url
    else None,
    config=virtual_end_node_config.provided,
  )

  # Updated server factory (accepts parameters to pass to OpenADRServer)
  openadr_server_factory = providers.Factory(OpenADRServer)

  virtual_top_node_config = providers.Factory(
    VirtualTopNodeConfig,
    vtn_id=config.adr_config.vtn_name,
    http_port=config.adr_config.openadr_http_port,
    http_host=config.adr_config.openadr_http_host,
    path_prefix=config.adr_config.openadr_vtn_path_prefix,
  )

  # Components (Tier 3)
  virtual_top_node = providers.Singleton(
    lambda config: VirtualTopNode(config)
    if config and config.http_host and config.http_port and config.path_prefix
    else None,
    config=virtual_top_node_config.provided,
    # sqlite_consumption_service=consumption_service
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

  node_component_controller = providers.Singleton(
    NodeComponentController, rest_service=rest_service, adr_service=adr_service
  )

  @staticmethod
  def create(application_config: ApplicationConfig):
    container = Container()
    print('', container.config)
    container.config.adr_config.from_dict(application_config.adr_config.__dict__)
    if application_config.mqtt_config is not None:
      container.config.mqtt_config.from_dict(application_config.mqtt_config.__dict__)
    if application_config.rest_config is not None:
      container.config.rest_config.from_dict(application_config.rest_config.__dict__)

    return container
