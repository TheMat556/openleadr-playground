from typing import Dict, List, Any, Optional

from injector import inject

from src.openadr_node import logger
from src.openadr_node.database.interfaces.repositories.iconsumption_repository import (
  IConsumptionRepository,
)
from src.openadr_node.database.interfaces.services.iconsumption_service import (
  IConsumptionService,
)


class ConsumptionService(IConsumptionService):
  @inject
  def __init__(self, repository: IConsumptionRepository):
    self.repository = repository

  def process_consumption_data(self, data: List[Dict[str, Any]]) -> None:
    """Process and save consumption data."""
    if not data:
      logger.warning('No consumption data provided')
      return
    self.repository.save_consumption_batch(data)

  def get_current_consumption(self, timestamp: int) -> Dict[str, Any]:
    """Get current consumption data for all VENs."""
    consumption_points = self.repository.get_closest_consumption_points(timestamp)
    if not consumption_points:
      raise ValueError('No consumption data available')

    overall_value = sum(point['value'] for point in consumption_points)

    return {
      'ven_id': consumption_points[0]['ven_id'],  # Using first VEN as reference
      'overall_value': overall_value,
      'unit': 'kWh',
      'timestamp': timestamp,
    }

  def get_closest_consumption_point(
    self, timestamp: int, ven_id: str, resource_id: str
  ) -> Optional[Dict[str, Any]]:
    """
    Get the closest consumption point for a specific VEN and resource.

    Args:
        timestamp (int): Target timestamp to find the closest point for
        ven_id (str): VEN ID to get consumption point for
        resource_id (str): Resource ID to get consumption point for

    Returns:
        Optional[Dict[str, Any]]: Dictionary containing the closest consumption point data
                                or None if no point is found
    """
    try:
      point = self.repository.get_closest_point(timestamp, ven_id, resource_id)
      if not point:
        return None

      return {
        'timestamp': point['timestamp'],
        'ven_id': point['ven_id'],
        'resource_id': point['resource_id'],
        'value': point['value'],
        'unit': 'kWh',
      }

    except Exception as e:
      logger.error(
        f'Failed to get closest consumption point for VEN {ven_id} and resource {resource_id}: {str(e)}'
      )
      raise

  def get_ven_count(self) -> int:
    """Get the count of unique VENs."""
    return self.repository.get_unique_vens()
