# src/openadr_node/exceptions/rest/exceptions.py
from src.openadr_node.communication.rest.exceptions.base import OpenADRBaseException


class RestServiceException(OpenADRBaseException):
  """Base exception for REST service errors"""

  def __init__(self, message: str, status_code: int = 500):
    super().__init__(message)
    self.status_code = status_code


class ServiceNotInitializedException(RestServiceException):
  def __init__(self, service_name: str):
    super().__init__(f'Service {service_name} not initialized', status_code=500)


class DataNotFoundException(RestServiceException):
  def __init__(self, data_type: str):
    super().__init__(f'{data_type} not found', status_code=404)


class DataProcessingException(RestServiceException):
  def __init__(self, operation: str, details: str):
    super().__init__(f'Failed to process {operation}: {details}', status_code=500)
