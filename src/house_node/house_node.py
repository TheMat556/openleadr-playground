from injector import Injector
from typing import List
import logging

from src.house_node.config import HouseNodeConfig
from src.openadr_node.dependency_injection.modules import ApplicationModule
from src.openadr_node.node_controller import NodeController
from src.openadr_node.models import ReportConfiguration

logger = logging.getLogger(__name__)


class HouseNode:
  def __init__(self, config: HouseNodeConfig):
    self.config = config
    self.reports: List[ReportConfiguration] = []
    self._setup_node()

  def _setup_node(self) -> None:
    app_config = self.config.to_application_config()
    injector = Injector([ApplicationModule(app_config)])
    self.node = injector.get(NodeController)

  def add_report(self, report: ReportConfiguration) -> None:
    self.reports.append(report)

  def add_reports(self, reports: List[ReportConfiguration]) -> None:
    self.reports.extend(reports)

  async def run(self) -> None:
    if self.reports:
      self.node.add_report(self.reports)
    try:
      await self.node.run()
    except Exception as e:
      logger.error(f'Error running node: {e}')
      raise
