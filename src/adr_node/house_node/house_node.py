from typing import List

from src.adr_node.core.dependency_injection.container import Container
from src.adr_node.house_node.config.house_node_config import HouseNodeConfig
from src.adr_node.config.report_config import ReportConfig


class HouseNode:
  def __init__(self, config: HouseNodeConfig):
    self.config = config
    self.reports: List[ReportConfig] = []
    self._container, self._component_controller = self._setup_node()

  def _setup_node(self):
    return Container.create(self.config.to_application_config())

  def get_adr_service(self):
    return self._container.adr_service()

  def add_report(self, report: ReportConfig) -> None:
    self.reports.append(report)

  def add_reports(self, reports: List[ReportConfig]) -> None:
    self.reports.extend(reports)

  def run(self) -> None:
    if self.reports:
      self.get_adr_service().add_reports(self.reports)
    try:
      self._component_controller.start()
    except Exception as _:
      # logger.error(f'Error running node: {e}')
      raise
