import asyncio
from injector import Module, singleton, provider

from ..communication.rest.interfaces.iflask_app_service import IFlaskAppService
from ..communication.rest.interfaces.irest_service import IRestService
from ..communication.rest.services.flask_app_service import FlaskAppService
from ..communication.rest.services.rest_service import RestService
from ..database import DatabaseManager, EnergyDatabaseController
from ..database.interfaces.database_interface import (
  IDatabaseManager,
  IEnergyDatabaseController,
)
from ..database.interfaces.repositories.iconsumption_repository import (
  IConsumptionRepository,
)
from ..database.interfaces.repositories.iload_profile_repository import (
  ILoadProfileRepository,
)
from ..database.interfaces.services.iconsumption_service import IConsumptionService
from ..database.interfaces.services.idatabase_service import IDatabaseService
from ..database.interfaces.services.iloadprofile_service import ILoadProfileService
from ..database.repositories.sqlite_consumption_repository import (
  SQLiteConsumptionRepository,
)
from ..database.repositories.sqlite_load_profile_repository import (
  SQLiteLoadProfileRepository,
)
from ..database.services.consumption_service import ConsumptionService
from ..database.services.database_service import SQLiteDatabaseService
from ..database.services.load_profile_service import LoadProfileService

from ..node_resource_controller import NodeResourceController
from ..node_open_adr_controller import NodeOpenADRController
from ..config.app_config import ApplicationConfig
from src.openadr_node.protocols.mqtt.interfaces.mqtt_interface import IMQTTController

from ..node_dispatcher_controller import NodeDispatcherController


class ApplicationModule(Module):
  def __init__(self, config: ApplicationConfig):
    print(config)
    self.config = config
    super().__init__()

  @singleton
  @provider
  def provide_config(self) -> ApplicationConfig:
    return self.config

  @singleton
  @provider
  def provide_database_manager(self) -> IDatabaseManager:
    return DatabaseManager(f'{self.config.node_id}.db')

  @singleton
  @provider
  def provide_energy_database_controller(
    self, db_manager: IDatabaseManager
  ) -> IEnergyDatabaseController:
    return EnergyDatabaseController(db_manager)

  # @singleton
  # @provider
  # def provide_rest_controller(
  #   self, config: ApplicationConfig, db_controller: IEnergyDatabaseController
  # ) -> IRestAPIController:
  #   if config.rest_api_config:
  #     rest_controller = RestAPIController(config.rest_api_config.port, db_controller)
  #     return rest_controller
  #   return None

  @singleton
  @provider
  def provide_flask_app_service(self, rest_service: IRestService) -> IFlaskAppService:
    return FlaskAppService(
      rest_service=rest_service, port=self.config.flask_app_service.port
    )

  @singleton
  @provider
  def provide_rest_service(
    self,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
  ) -> IRestService:
    return RestService(load_profile_service, consumption_service)

  @singleton
  @provider
  def provide_mqtt_controller(
    self, config: ApplicationConfig, db_controller: IEnergyDatabaseController
  ) -> IMQTTController:
    if config.mqtt_config:
      return MQTTController(config.mqtt_config, db_controller, config.ven_name)  # noqa: F821
    return None

  @singleton
  @provider
  def provide_resource_controller(
    self, db_controller: IEnergyDatabaseController
  ) -> NodeResourceController:
    return NodeResourceController(db_controller)

  @provider
  def provide_dispatcher_controller(self) -> NodeDispatcherController:
    return NodeDispatcherController()

  @provider
  def provide_open_adr_controller(
    self, config: ApplicationConfig
  ) -> NodeOpenADRController:
    # Get or create event loop
    try:
      loop = asyncio.get_event_loop()
    except RuntimeError:
      loop = asyncio.new_event_loop()
      asyncio.set_event_loop(loop)

    return NodeOpenADRController(
      loop=loop,
      vtn_name=config.vtn_name,
      ven_name=config.ven_name,
      vtn_url=config.vtn_url,
      openadr_http_host=config.openadr_http_host,
      openadr_http_port=config.openadr_http_port,
      openadr_vtn_path_prefix=config.openadr_vtn_path_prefix,
    )

  @singleton
  @provider
  def provide_database_service(self) -> IDatabaseService:
    return SQLiteDatabaseService(f'{self.config.node_id}.db')

  @singleton
  @provider
  def provide_load_profile_repository(
    self, database_service: IDatabaseService
  ) -> ILoadProfileRepository:
    return SQLiteLoadProfileRepository(database_service)

  @singleton
  @provider
  def provide_consumption_repository(
    self, database_service: IDatabaseService
  ) -> IConsumptionRepository:
    return SQLiteConsumptionRepository(database_service)

  @singleton
  @provider
  def provide_load_profile_service(
    self, repository: ILoadProfileRepository
  ) -> ILoadProfileService:
    return LoadProfileService(repository)  # Implement your actual service

  @singleton
  @provider
  def provide_consumption_service(
    self, repository: IConsumptionRepository
  ) -> IConsumptionService:
    return ConsumptionService(repository)  # Implement your actual service
