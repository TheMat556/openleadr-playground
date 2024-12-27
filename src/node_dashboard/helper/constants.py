import os
from enum import Enum

MAX_BUFFER_SIZE = int(os.getenv('MAX_BUFFER_SIZE', 96))
LOAD_PROFILE_UPDATE_INTERVAL = int(os.getenv('LOAD_PROFILE_UPDATE_INTERVAL', 5))
CONSUMPTION_UPDATE_INTERVAL = int(os.getenv('CONSUMPTION_UPDATE_INTERVAL', 5))


class Environment(str, Enum):
  LOCAL = 'false'
  DOCKER = 'true'
