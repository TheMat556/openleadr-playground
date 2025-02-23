from typing import Dict, List, Any, Optional
import logging
import numpy as np

from src.adr_node.database.interfaces.repositories.ih_load_profile_repository import (
  IHLoadProfileRepository,
)
from src.adr_node.database.interfaces.services.ih_load_profile_service import (
  IHLoadProfileService,
)


class HLoadProfileService(IHLoadProfileService):
  """
  Service for managing H-load profile data.
  Last updated: 2025-02-21 16:10:36 UTC by TheMat556

  Attributes
  ----------
  repository : IHLoadProfileRepository
      The repository used for data access.
  """

  def __init__(self, repository: IHLoadProfileRepository):
    self.repository = repository

  def save_h_load_profile(
    self, data: List[Dict[str, Any]], ven_id: Optional[str] = None
  ) -> Dict[str, Any]:
    """
    Save H-load profile data.

    Args:
        data: List of dictionaries containing timestamp and value pairs
        ven_id: Optional VEN ID to associate with the data points

    Returns:
        Dict containing success and failure counts and any errors
    """
    if not data:
      logging.warning('No data provided for saving H-load profile')
      return {'success': 0, 'failed': 0, 'errors': []}
    return self.repository.save_h_load_profile(data, ven_id=ven_id)

  def get_h_load_profile(
    self,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order_by: str = 'timestamp ASC',
    ven_id: Optional[str] = None,
    timestamp: Optional[int] = None,
  ) -> Dict[str, np.ndarray]:
    """
    Retrieve H-load profile data.

    Args:
        limit: Optional limit on number of records
        offset: Optional offset for pagination
        order_by: SQL ORDER BY clause
        ven_id: Optional VEN ID to filter by
        timestamp: Optional timestamp to filter by

    Returns:
        Dict containing numpy arrays of timestamps, values, and ven_ids
    """
    return self.repository.get_h_load_profile(
      limit=limit, offset=offset, order_by=order_by, ven_id=ven_id
    )

  def get_current_h_load_profile(
    self, ven_id: Optional[str] = None
  ) -> Optional[Dict[str, Any]]:
    """
    Get the current H-load profile value.

    Args:
        ven_id: Optional VEN ID to filter the results

    Returns:
        Optional dict containing the most recent profile data
    """
    return self.repository.get_current_h_load_profile(ven_id=ven_id)
