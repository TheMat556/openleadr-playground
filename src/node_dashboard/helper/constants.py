from enum import Enum

MAX_BUFFER_SIZE = 96
LOAD_PROFILE_UPDATE_INTERVAL = 5
CONSUMPTION_UPDATE_INTERVAL = 5

class Environment(str, Enum):
    LOCAL = 'false'
    DOCKER = 'true'
