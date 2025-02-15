from dataclasses import dataclass
from typing import Optional


@dataclass
class ZValueQuery:
  """
  Query parameters for z-value searches.

  Attributes
  ----------
  timestamp_start : Optional[int]
      Start timestamp for the query.
  timestamp_end : Optional[int]
      End timestamp for the query.
  ven_id : Optional[str]
      VEN ID to filter the query.
  limit : int
      Limit on the number of results.
  offset : int
      Offset for the query results.
  order_by : str
      Field to order the results by.
  order_direction : str
      Direction to order the results ('ASC' or 'DESC').
  """

  timestamp_start: Optional[int] = None
  timestamp_end: Optional[int] = None
  ven_id: Optional[str] = None
  limit: int = 100
  offset: int = 0
  order_by: str = 'timestamp'
  order_direction: str = 'DESC'
