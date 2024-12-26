import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


async def fetch_data_with_retry(
  session: aiohttp.ClientSession, url: str, max_retries: int = 3, timeout: int = 10
) -> Optional[Dict[str, Any]]:
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
      await asyncio.sleep(2**attempt)


async def fetch_data_async(
  session: aiohttp.ClientSession, url: str
) -> Optional[Dict[str, Any]]:
  return await fetch_data_with_retry(session, url)


def round_to_nearest_minute(dt: datetime) -> datetime:
  return dt.replace(second=0, microsecond=0) + timedelta(minutes=dt.second // 30)
