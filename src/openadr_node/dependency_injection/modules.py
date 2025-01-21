import asyncio
from injector import Module, singleton, provider
from ..database.interfaces.database_interface import (
  IDatabaseManager,
  IEnergyDatabaseController,
  IRestAPIController,
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
from ..database.services.database_manager import DatabaseManager
from ..database.services.database_service import SQLiteDatabaseService
from ..database.services.energy_database_controller import (
  EnergyDatabaseController,
)
from ..database.services.load_profile_service import LoadProfileService
from ..node_resource_controller import NodeResourceController
from ..node_open_adr_controller import NodeOpenADRController
from ..config.app_config import ApplicationConfig

from src.openadr_node.communication.rest.rest_manager import RestAPIController
from src.openadr_node.mqtt_controller import (
  MQTTManager,
)
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
  def provide_database_service(self) -> IDatabaseService:
    return SQLiteDatabaseService(f'{self.config.node_id}.db')

  @singleton
  @provider
  def provide_load_profile_repository(
    self, database_service: IDatabaseService
  ) -> SQLiteLoadProfileRepository:
    return SQLiteLoadProfileRepository(database_service)

  @singleton
  @provider
  def provide_consumption_repository(
    self, database_service: IDatabaseService
  ) -> SQLiteConsumptionRepository:
    return SQLiteConsumptionRepository(database_service)

  @singleton
  @provider
  def provide_load_profile_service(
    self, repository: SQLiteLoadProfileRepository
  ) -> ILoadProfileService:
    return LoadProfileService(repository)

  @singleton
  @provider
  def provide_consumption_service(
    self, repository: SQLiteConsumptionRepository
  ) -> IConsumptionService:
    return ConsumptionService(repository)

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

  @singleton
  @provider
  def provide_rest_controller(
    self,
    config: ApplicationConfig,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
  ) -> IRestAPIController:
    if config.flask_app_service:
      rest_controller = RestAPIController(
        config.flask_app_service.port, load_profile_service, consumption_service
      )
      return rest_controller
    return None

  @singleton
  @provider
  def provide_mqtt_controller(
    self,
    config: ApplicationConfig,
    load_profile_service: ILoadProfileService,
    consumption_service: IConsumptionService,
  ) -> MQTTManager:
    if config.mqtt_config:
      mqtt_controller = MQTTManager(
        config.mqtt_config,
      )
      return mqtt_controller
    return None

  @singleton
  @provider
  def provide_resource_controller(
    self, db_controller: IEnergyDatabaseController
  ) -> NodeResourceController:
    return NodeResourceController(db_controller)

  @singleton
  @provider
  def provide_dispatcher_controller(self) -> NodeDispatcherController:
    return NodeDispatcherController()

  @singleton
  @provider
  def provide_open_adr_controller(
    self, config: ApplicationConfig
  ) -> NodeOpenADRController:
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
