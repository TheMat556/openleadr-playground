from abc import abstractmethod, ABC
from typing import Any

from src.adr_node.core.interfaces.irunable import IRunnable


class IVirtualTopNode(ABC, IRunnable):
  """
  Interface for Virtual Top Node (VTN) in the OpenADR system.

  This interface defines the methods that must be implemented by any
  Virtual Top Node class.

  Methods
  -------
  run() -> Any
      Get the OpenADR server run method.
  handle_device_status(ven_id: str, opt_type: str) -> None
      Handle device status changes.
  event_response_callback(ven_id: str, event_id: str, opt_type: str) -> None
      Handle event responses.
  """

  @abstractmethod
  def run(self) -> Any:
    """
    Get the OpenADR server run method.

    Returns
    -------
    Any
        The result of the server run method.
    """
    pass

  @abstractmethod
  async def handle_device_status(self, ven_id: str, opt_type: str) -> None:
    """
    Handle device status changes.

    Parameters
    ----------
    ven_id : str
        The VEN ID.
    opt_type : str
        The opt type.
    """
    pass

  @abstractmethod
  async def event_response_callback(
    self, ven_id: str, event_id: str, opt_type: str
  ) -> None:
    """
    Handle event responses.

    Parameters
    ----------
    ven_id : str
        The VEN ID.
    event_id : str
        The event ID.
    opt_type : str
        The opt type.
    """
    pass
