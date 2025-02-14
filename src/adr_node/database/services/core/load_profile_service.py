from typing import Dict, List, Any, Optional

import numpy as np

from src.adr_node.database.interfaces.repositories.iload_profile_repository import (
  ILoadProfileRepository,
)
from src.adr_node.database.interfaces.services.iloadprofile_service import (
  ILoadProfileService,
)
from src.openadr_node import logger


class LoadProfileService(ILoadProfileService):
  def __init__(self, repository: ILoadProfileRepository):
    self.repository = repository

  def save_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not data:
      logger.warning('No data provided for saving load profile')
      return {'success': 0, 'failed': 0, 'errors': []}
    return self.repository.save_load_profile(data)

  def process_load_profile(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Process and save load profile data."""
    if not data:
      logger.warning('No data provided for processing')
      return {'success': 0, 'failed': 0, 'errors': []}

    return self.repository.save_load_profile(data)

  def get_load_profile_data(
    self, limit: Optional[int] = None, offset: Optional[int] = None
  ) -> Dict[str, np.ndarray]:
    """Retrieve load profile data with optional pagination."""
    return self.repository.get_load_profile(limit=limit, offset=offset)

  def get_closest_load_point(self, timestamp: int) -> Optional[Dict[str, Any]]:
    """Get the closest load profile point to the given timestamp."""
    return self.repository.get_closest_point(timestamp)
