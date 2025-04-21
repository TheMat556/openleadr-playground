# src/adr_node/core/services/distribution/generators/time_interval_generator.py
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any
import numpy as np

from ..interfaces.itime_interval_generator import ITimeIntervalGenerator


class TimeIntervalGenerator(ITimeIntervalGenerator):
  """
  Time Interval Generator for the OpenADR system.

  This class provides methods to generate time intervals for the ADR system.

  Attributes
  ----------
  INTERVAL_DURATION_MS : int
      Duration of each interval in milliseconds (default is 15 minutes).
  INTERVALS_PER_DAY : int
      Number of intervals per day (default is 1).
  GMT_PLUS_ONE : timezone
      Timezone offset for GMT+1.
  """

  INTERVAL_DURATION_MS: int = 900000  # 15 minutes
  INTERVALS_PER_DAY: int = 1
  GMT_PLUS_ONE = timezone(timedelta(hours=2))

  def generate_intervals(self) -> List[Dict[str, Any]]:
    """
    Generate time intervals for the ADR system.

    Returns
    -------
    List[Dict[str, Any]]
        List of dictionaries containing interval start time, duration, and signal payload.
    """
    gmt_plus_one_now = datetime.now(self.GMT_PLUS_ONE)
    second = (gmt_plus_one_now.second // 30) * 30
    start_of_day = gmt_plus_one_now.replace(second=second, microsecond=0)
    base_timestamp = int(start_of_day.timestamp())

    intervals = np.arange(self.INTERVALS_PER_DAY) * self.INTERVAL_DURATION_MS

    return [
      {
        'dstart': base_timestamp + int(offset),
        'duration': self.INTERVAL_DURATION_MS,
        'signal_payload': 0,
      }
      for offset in intervals
    ]
