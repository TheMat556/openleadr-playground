import logging
from datetime import datetime, timedelta
import aiohttp
import asyncio
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)


async def fetch_data_with_retry(
  session: aiohttp.ClientSession, url: str, max_retries: int = 3, timeout: int = 10
) -> Optional[Dict[str, Any]]:
  """
  Fetch data from the given URL with retry logic and exponential backoff.

  Parameters
  ----------
  session : aiohttp.ClientSession
      The aiohttp session to use for making the request.
  url : str
      The URL to fetch data from.
  max_retries : int, optional
      The maximum number of retry attempts (default is 3).
  timeout : int, optional
      The timeout for each request in seconds (default is 10).

  Returns
  -------
  Optional[Dict[str, Any]]
      The fetched data as a dictionary, or None if the request failed.
  """
  for attempt in range(max_retries):
    try:
      async with session.get(url, timeout=timeout) as response:
        response.raise_for_status()
        return await response.json()
    except aiohttp.ClientError as e:
      if attempt == max_retries - 1:
        logger.error(
          f'Failed to fetch data after {max_retries} attempts: {e} from {url}'
        )
        return None
      else:
        logger.warning(f'Attempt {attempt + 1}/{max_retries} failed: {e}. Retrying...')
      await asyncio.sleep(2**attempt)


async def fetch_data_async(
  session: aiohttp.ClientSession, url: str
) -> Optional[Dict[str, Any]]:
  """
  Fetch data asynchronously from the given URL.

  Parameters
  ----------
  session : aiohttp.ClientSession
      The aiohttp session to use for making the request.
  url : str
      The URL to fetch data from.

  Returns
  -------
  Optional[Dict[str, Any]]
      The fetched data as a dictionary, or None if the request failed.
  """
  return await fetch_data_with_retry(session, url)


def round_to_nearest_minute(dt: datetime) -> datetime:
  """
  Rounds a datetime object to the nearest minute.

  This function rounds a datetime object to the nearest minute.
  If the seconds value is 30 or more, it rounds up to the next minute.
  Otherwise, it rounds down to the current minute.

  Parameters
  ----------
  dt : datetime
      The datetime object to be rounded.

  Returns
  -------
  datetime
      The rounded datetime object.
  """
  if dt.second >= 30:
    return dt.replace(second=0, microsecond=0) + timedelta(minutes=1)
  else:
    return dt.replace(second=0, microsecond=0)


def parse_time_to_datetime(time_str: str, timezone: Optional[str] = None) -> datetime:
  today_str = datetime.now().strftime('%Y-%m-%d')
  timestamp_str = f'{today_str}T{time_str}:00'
  dt = datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
  if timezone:
    from zoneinfo import ZoneInfo

    dt = dt.replace(tzinfo=ZoneInfo(timezone))
  return dt
