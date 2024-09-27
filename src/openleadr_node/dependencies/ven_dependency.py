import random

from src.openleadr_node.dependencies.venInterface import VenDependencyInterface


class VenDependency(VenDependencyInterface):
  def handle_collect_report_value(self):
    return random.uniform(1.0, 100.0)
