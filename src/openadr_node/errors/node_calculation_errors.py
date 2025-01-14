from typing import Optional, Dict, Any


class CalculationError(Exception):
  """Base exception for calculation-related errors."""

  def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
    super().__init__(message)
    self.details = details or {}

  pass


class ValidationError(CalculationError):
  """Raised when data validation fails."""

  pass


class ProcessingError(CalculationError):
  """Raised when data processing fails."""

  pass
