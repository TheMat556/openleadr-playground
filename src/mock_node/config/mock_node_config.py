from dataclasses import dataclass
from src.openadr_node.config.app_config import ApplicationConfig
from src.openadr_node.models.rest_config import RestApiConfig


@dataclass
class MockNodeConfig:
  """Mock node configuration"""

  node_id: str
  vtn_name: str = 'default_vtn'
  openadr_http_host: str = (None,)
  openadr_http_port: int = (None,)
  openadr_vtn_path_prefix: str = '/OpenADR2/Simple/2.0b'
  rest_api_port: int = 5000
  gradio_port: int = 7860
  gradio_host: str = '0.0.0.0'
  slider_file: str = '../slider_values.txt'

  def to_application_config(self) -> ApplicationConfig:
    return ApplicationConfig(
      node_id=self.node_id,
      vtn_name=self.vtn_name,
      openadr_http_host=self.openadr_http_host,
      openadr_http_port=self.openadr_http_port,
      openadr_vtn_path_prefix=self.openadr_vtn_path_prefix,
      rest_api_config=RestApiConfig(port=self.rest_api_port),
    )
