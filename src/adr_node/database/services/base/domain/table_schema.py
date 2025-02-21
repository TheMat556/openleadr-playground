from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class TableSchema:
  """
  Schema definition for a database table.

  Attributes
  ----------
  name : str
      The name of the table.
  columns : Dict[str, str]
      A dictionary mapping column names to their data types.
  indexes : Optional[Dict[str, str]]
      A dictionary mapping index names to their definitions.
  """

  name: str
  columns: Dict[str, str]
  indexes: Optional[Dict[str, str]] = None
