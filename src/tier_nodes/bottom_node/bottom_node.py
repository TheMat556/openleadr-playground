from typing import List

from src.adr_node.core.dependency_injection.container import Container
from src.adr_node.config.report_config import ReportConfig
from src.tier_nodes.bottom_node.config.bottom_node_config import BottomNodeConfig


class BottomNode:
  """
  BottomNode class to manage the configuration and reports for the bottom node.

  :param config: Configuration for the bottom node.
  :type config: BottomNodeConfig
  """

  def __init__(self, config: BottomNodeConfig):
    self.config = config
    self.reports: List[ReportConfig] = []
    self._container, self._component_controller = self._setup_node()

  def _setup_node(self):
    """
    Set up the node by creating the container and component controller.

    :return: Tuple containing the container and component controller.
    :rtype: Tuple[Container, Any]
    """
    return Container.create(self.config.to_application_config())

  def get_adr_service(self):
    """
    Get the ADR service from the container.

    :return: ADR service instance.
    :rtype: Any
    """
    return self._container.adr_service()

  def add_report(self, report: ReportConfig) -> None:
    """
    Add a single report to the node.

    :param report: Report configuration to add.
    :type report: ReportConfig
    """
    self.reports.append(report)

  def add_reports(self, reports: List[ReportConfig]) -> None:
    """
    Add multiple reports to the node.

    :param reports: List of report configurations to add.
    :type reports: List[ReportConfig]
    """
    self.reports.extend(reports)

  def run(self) -> None:
    """
    Run the node by starting the component controller and adding reports if available.

    :raises Exception: If an error occurs while running the node.
    """
    if self.reports:
      self.get_adr_service().add_reports(self.reports)
    try:
      self._component_controller.start()
    except Exception as e:
      self.logger.error(f'Error running node: {e}')
      raise
