from dataclasses import dataclass
from typing import Optional


@dataclass
class AdrConfig:
  """
  Configuration for the Automated Demand Response (ADR) component.

  This class holds the configuration details required for the ADR component.

  Attributes
  ----------
  node_id : Optional[str]
      The ID of the node.
  vtn_name : Optional[str]
      The name of the Virtual Top Node (VTN).
  ven_name : Optional[str]
      The name of the Virtual End Node (VEN).
  vtn_url : Optional[str]
      The URL of the VTN.
  openadr_http_host : Optional[str]
      The HTTP host for OpenADR.
  openadr_http_port : Optional[int]
      The HTTP port for OpenADR.
  openadr_vtn_path_prefix : Optional[str]
      The path prefix for the VTN.
  """

  node_id: Optional[str] = None
  vtn_name: Optional[str] = None
  ven_name: Optional[str] = None
  vtn_url: Optional[str] = None
  openadr_http_host: Optional[str] = None
  openadr_http_port: Optional[int] = None
  openadr_vtn_path_prefix: Optional[str] = None
