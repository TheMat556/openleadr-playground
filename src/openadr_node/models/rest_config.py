from dataclasses import dataclass


@dataclass
class RestApiConfig:
  """
  Configuration settings for REST API.

  Attributes
  ----------
  port : int
      The port number for the REST API.
  """

  port: int
