from enum import Enum, auto


class SignalType(Enum):
  """Signal types for inter-service communication."""

  SYSTEM_READY = auto()
  LOAD_PROFILE_UPDATED = auto()
  ERROR_OCCURRED = auto()
