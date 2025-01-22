from abc import abstractmethod
from typing import Optional, List

from src.adr_node.core.interfaces.irunable import IRunnable
from src.openadr_node.models import ReportConfiguration


class IAdrService(IRunnable):
  @abstractmethod
  def create_node_tasks(self) -> None:
    pass

  @abstractmethod
  def shutdown(self) -> None:
    pass

  @abstractmethod
  def add_reports(
    self, list_of_reports: Optional[List[ReportConfiguration]] = None
  ) -> None:
    pass

  @abstractmethod
  async def _process_report_queue(self) -> None:
    pass
