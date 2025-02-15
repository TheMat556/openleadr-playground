from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.nodes.domains.report_configuration import ReportConfiguration


class IVirtualEndNode(ABC, IRunnable):
  """
  Interface for Virtual End Node (VEN) in the OpenADR system.

  This interface defines the methods that must be implemented by any
  Virtual End Node class.

  Methods
  -------
  register_base_report() -> None
      Register the base report for the VEN.
  add_reports(reports: Optional[List[ReportConfiguration]] = None) -> None
      Add reports to the VEN.
  handle_event(event: Dict[str, Any]) -> str
      Handle an OpenADR event.
  get_data() -> float
      Get the base consumption data.
  """

  @abstractmethod
  def register_base_report(self) -> None:
    """
    Register the base report for the Virtual End Node (VEN).

    This method should contain the logic to register the base report.
    """
    pass

  @abstractmethod
  def add_reports(self, reports: Optional[List[ReportConfiguration]] = None) -> None:
    """
    Add reports to the Virtual End Node (VEN).

    Parameters
    ----------
    reports : Optional[List[ReportConfiguration]]
        List of report configurations to add.
    """
    pass

  @abstractmethod
  async def handle_event(self, event: Dict[str, Any]) -> str:
    """
    Handle an OpenADR event.

    Parameters
    ----------
    event : Dict[str, Any]
        The OpenADR event data.

    Returns
    -------
    str
        The response to the event.
    """
    pass

  @abstractmethod
  def get_data(self) -> float:
    """
    Get the base consumption data.

    Returns
    -------
    float
        The base consumption data.
    """
    pass
