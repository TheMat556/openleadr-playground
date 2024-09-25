import os

from dependency_injector import containers, providers


class Config:
    def __init__(self, initial_ven_id: int):
        self.ven_id = initial_ven_id
        self.ven_name = os.getenv("DB_NAME")
        # add additional configs....

    def set_ven_id(self, new_ven_id: int):
        self.ven_id = new_ven_id

    def get_ven_id(self):
        return self.ven_id


class Container(containers.DeclarativeContainer):
    config = providers.Singleton(Config, initial_ven_id=100)
