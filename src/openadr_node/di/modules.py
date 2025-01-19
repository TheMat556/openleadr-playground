import asyncio
from injector import Module, singleton, provider
from ..database.interfaces.database_interface import (
  IDatabaseManager,
  IEnergyDatabaseController,
  IRestAPIController,
)
from ..database.implementations.database_manager import DatabaseManager
from ..database.implementations.energy_database_controller import (
  EnergyDatabaseController,
)
from ..node_resource_controller import NodeResourceController
from ..node_open_adr_controller import NodeOpenADRController
from ..config.app_config import ApplicationConfig
from src.openadr_node.protocols.mqtt.interfaces.mqtt_interface import IMQTTController
from ..protocols.rest_manager import RestAPIController
from src.openadr_node.protocols.mqtt.implementation.mqtt_controller import (
  MQTTController,
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
    self, config: ApplicationConfig, db_controller: IEnergyDatabaseController
  ) -> IRestAPIController:
    if config.rest_api_config:
      rest_controller = RestAPIController(config.rest_api_config.port, db_controller)
      return rest_controller
    return None

  @singleton
  @provider
  def provide_mqtt_controller(
    self, config: ApplicationConfig, db_controller: IEnergyDatabaseController
  ) -> IMQTTController:
    if config.mqtt_config:
      return MQTTController(config.mqtt_config, db_controller, config.ven_name)
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
