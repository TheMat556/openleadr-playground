class RestServiceException(Exception):
  """Base exception for REST service"""

  pass


class ServiceStartupError(RestServiceException):
  """Raised when the service fails to start"""

  pass


class ServiceShutdownError(RestServiceException):
  """Raised when the service fails to shutdown"""

  pass
