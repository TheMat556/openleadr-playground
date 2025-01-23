from dataclasses import dataclass
from typing import Dict


@dataclass
class TableSchema:
  name: str
  columns: Dict[str, str]
  indexes: Dict[str, str] = None
