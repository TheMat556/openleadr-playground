from abc import abstractmethod
from typing import Optional, List

from src.adr_node.core.interfaces.irunable import IRunnable
from src.adr_node.core.nodes.domains.report_configuration import ReportConfiguration


class IAdrService(IRunnable):
  """
  Interface for ADR Service in the OpenADR system.

  This interface defines the methods that must be implemented by any
  ADR Service class.

  Methods
  -------
  create_node_tasks() -> None
      Create tasks for the ADR node.
  shutdown() -> None
      Shutdown the ADR service.
  add_reports(list_of_reports: Optional[List[ReportConfiguration]] = None) -> None
      Add reports to the ADR service.
  _process_report_queue() -> None
      Process the report queue asynchronously.
  """

  @abstractmethod
  def create_node_tasks(self) -> None:
    """
    Create tasks for the ADR node.
    """
    pass

  @abstractmethod
  def shutdown(self) -> None:
    """
    Shutdown the ADR service.
    """
    pass

  @abstractmethod
  def add_reports(
    self, list_of_reports: Optional[List[ReportConfiguration]] = None
  ) -> None:
    """
    Add reports to the ADR service.

    Parameters
    ----------
    list_of_reports : Optional[List[ReportConfiguration]]
        List of report configurations to add.
    """
    pass

  @abstractmethod
  async def _process_report_queue(self) -> None:
    """
    Process the report queue asynchronously.
    """
    pass
