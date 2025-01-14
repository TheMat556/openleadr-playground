from typing import Optional, Any, Dict


class NodeControllerError(Exception):
  """Base exception class for NodeResourceController errors."""

  def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
    super().__init__(message)
    self.details = details or {}


class LoadProfileError(NodeControllerError):
  """Raised when there's an error updating or processing load profiles."""

  pass


class ConsumptionError(NodeControllerError):
  """Raised when there's an error processing consumption data."""

  pass
