from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import numpy as np


class IHLoadProfileService(ABC):
  """
  Interface for H-load profile service operations.
  Last updated: 2025-02-21 16:10:36 UTC by TheMat556
  """

  @abstractmethod
  def save_h_load_profile(
    self, data: List[Dict[str, Any]], ven_id: Optional[str] = None
  ) -> Dict[str, Any]:
    """
    Save H-load profile data.

    Args:
        data: List of dictionaries containing at minimum:
            - timestamp (int): Unix timestamp
            - value (float): The profile value
        ven_id: Optional VEN ID to associate with the data points.
               If None, creates/updates base profile entries.

    Returns:
        Dict containing:
            - success (int): Number of successfully saved entries
            - failed (int): Number of failed entries
            - errors (List): List of any errors encountered
    """
    pass

  @abstractmethod
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
        limit: Maximum number of records to return
        offset: Number of records to skip for pagination
        order_by: SQL ORDER BY clause
        ven_id: Optional VEN ID to filter results
        timestamp: Optional timestamp to filter results

    Returns:
        Dict containing:
            - timestamp (np.ndarray): Array of Unix timestamps
            - value (np.ndarray): Array of corresponding values
            - ven_ids (np.ndarray): Array of corresponding VEN IDs
    """
    pass

  @abstractmethod
  def get_current_h_load_profile(
    self, ven_id: Optional[str] = None
  ) -> Optional[Dict[str, Any]]:
    """
    Get the most recent H-load profile value.

    Args:
        ven_id: Optional VEN ID to filter results.
               If None, returns most recent base profile value.

    Returns:
        Optional[Dict] containing:
            - timestamp (int): Unix timestamp of the entry
            - value (float): Profile value
            - ven_id (str, optional): VEN ID if applicable
        Returns None if no profile exists.
    """
    pass
