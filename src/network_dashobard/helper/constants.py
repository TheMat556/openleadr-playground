from typing import Final

# Update intervals (in seconds)
UPDATE_INTERVAL: Final[float] = 10.0
LOAD_PROFILE_UPDATE_INTERVAL: Final[float] = 10.0
MAX_BUFFER_SIZE: Final[int] = 1000


# Environment settings
class Environment:
  LOCAL: Final[str] = 'local'
  DOCKER: Final[str] = 'docker'
  PRODUCTION: Final[str] = 'production'


# API endpoints
class APIEndpoints:
  CONSUMPTION: Final[str] = 'consumption'
  LOAD_PROFILE: Final[str] = 'load-profile'


# UI Settings
class UISettings:
  DEFAULT_THEME: Final[str] = 'dark'
  SIDEBAR_SCALE: Final[int] = 1
  MAIN_CONTENT_SCALE: Final[int] = 4
  DEFAULT_PORT: Final[int] = 7860


# Plot Settings
class PlotSettings:
  COLORS = {
    'blue': (24, 115, 250),
    'orange': (250, 115, 24),
    'green': (24, 250, 115),
    'red': (250, 24, 24),
  }
  MARKER_SIZE: Final[int] = 8
  LINE_WIDTH: Final[int] = 2
