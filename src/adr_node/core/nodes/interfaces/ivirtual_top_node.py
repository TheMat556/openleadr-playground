from abc import abstractmethod, ABC
from typing import Any

from src.adr_node.core.interfaces.irunable import IRunnable


class IVirtualTopNode(ABC, IRunnable):
  """Interface for VirtualTopNode defining required methods"""

  @abstractmethod
  def run(self) -> Any:
    """Get the OpenADR server run method"""
    pass

  @abstractmethod
  async def handle_device_status(self, ven_id: str, opt_type: str) -> None:
    """Handle device status changes"""
    pass

  @abstractmethod
  async def event_response_callback(
    self, ven_id: str, event_id: str, opt_type: str
  ) -> None:
    """Handle event responses"""
    pass
