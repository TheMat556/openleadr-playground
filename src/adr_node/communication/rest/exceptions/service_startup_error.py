from src.adr_node.communication.rest.exceptions.rest_service_exception import (
  RestServiceException,
)


class ServiceStartupError(RestServiceException):
  """Raised when the service fails to start"""

  pass
