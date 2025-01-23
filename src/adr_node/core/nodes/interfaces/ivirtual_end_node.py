from abc import ABC, abstractmethod
from typing import Any, List, Dict, Optional

from src.adr_node.core.interfaces.irunable import IRunnable
from src.openadr_node.models import ReportConfiguration


class IVirtualEndNode(ABC, IRunnable):
  @abstractmethod
  def register_base_report(self) -> None:
    pass

  @abstractmethod
  def add_reports(self, reports: Optional[List[ReportConfiguration]] = None) -> None:
    pass

  @abstractmethod
  def handle_event(self, event: Dict[str, Any]) -> str:
    pass

  @abstractmethod
  def get_data(self) -> float:
    pass
