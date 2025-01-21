# src/openadr_node/protocols/rest/interfaces/irest_service.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple


class IRestService(ABC):
  @abstractmethod
  def get_load_profile(self) -> Tuple[Dict[str, Any], int]:
    """Get load profile data"""
    pass

  @abstractmethod
  def get_current_consumption(self) -> Tuple[Dict[str, Any], int]:
    """Get current consumption data"""
    pass
