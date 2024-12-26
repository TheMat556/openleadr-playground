import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)


async def fetch_data_async(
  session: aiohttp.ClientSession, url: str
) -> Optional[Dict[str, Any]]:
  logger.info(f'Fetching data from {url}')
  try:
    async with session.get(url, timeout=10) as response:
      response.raise_for_status()
      return await response.json()
  except aiohttp.ClientError as e:
    logger.error(f'Failed to fetch data: {e} from {url}')
    return None


def round_to_nearest_minute(dt: datetime) -> datetime:
  return dt.replace(second=0, microsecond=0) + timedelta(minutes=dt.second // 30)
