from injector import singleton, provider, Module
from .interfaces.database_interface import IDatabaseManager, IEnergyDatabaseController
from .implementations.database_manager import DatabaseManager
from .implementations.energy_database_controller import EnergyDatabaseController


class DatabaseModule(Module):
  @singleton
  @provider
  def provide_database_manager(self) -> IDatabaseManager:
    return DatabaseManager('energy.db')

  @singleton
  @provider
  def provide_energy_database_controller(
    self, db_manager: IDatabaseManager
  ) -> IEnergyDatabaseController:
    return EnergyDatabaseController(db_manager)
