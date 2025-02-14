from abc import abstractmethod
from dataclasses import dataclass


@dataclass
class IRunnable:
  @abstractmethod
  def run(self):
    pass
