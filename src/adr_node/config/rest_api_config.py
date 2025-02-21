from dataclasses import dataclass


@dataclass
class RestApiConfig:
  """
  Configuration settings for REST API.

  Attributes
  ----------
  port : int
      The port number for the REST API.
  host : str
      The host address for the REST API.
  """

  port: int
  host: str = '0.0.0.0'
