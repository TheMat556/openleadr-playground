from datetime import datetime, timezone
from typing import Dict, Any, List

from src.adr_node.communication.rest.routes.decorators.route_decorator import api_route
from src.openadr_node import logger


class ConsumptionHandler:
  def __init__(self, consumption_service):
    self.consumption_service = consumption_service

  def _process_consumption_points(self, points: List[Any]) -> Dict[str, Any]:
    """
    Process consumption points to calculate totals and organize data.

    Args:
        points: List of ConsumptionData objects

    Returns:
        Dict containing processed consumption data
    """
    if not points:
      raise ValueError('No consumption points available')

    # Calculate total consumption value
    total_value = sum(point.value for point in points)

    # Group consumption by VEN
    ven_consumption = {}
    for point in points:
      if point.ven_id not in ven_consumption:
        ven_consumption[point.ven_id] = {'value': 0, 'points': []}
      ven_consumption[point.ven_id]['value'] += point.value
      ven_consumption[point.ven_id]['points'].append(
        {
          'timestamp': point.timestamp,
          'value': point.value,
          'resource_id': point.resource_id,
        }
      )

    return {
      'total_consumption': total_value,
      'ven_count': len(ven_consumption),
      'unit': 'kWh',
      'ven_details': ven_consumption,
    }

  @api_route('/api/consumption', methods=['GET'])
  def get_current_consumption(self):
    """Get current consumption data for all VENs with totals."""
    try:
      timestamp = int(datetime.now(timezone.utc).timestamp())
      result = self.consumption_service.get_closest_consumption_points(
        target_timestamp=timestamp
      )

      if not result.success:
        raise ValueError(result.error)

      if not result.data.get('consumption_points'):
        raise ValueError('No consumption points found')

      consumption_points = result.data['consumption_points']
      processed_data = self._process_consumption_points(consumption_points)

      return {
        'timestamp': timestamp,
        'overall_value': processed_data['total_consumption'],
        'unit': processed_data['unit'],
        'ven_count': processed_data['ven_count'],
        'ven_details': processed_data['ven_details'],
        'last_updated': datetime.now(timezone.utc).isoformat(),
      }

    except Exception as e:
      logger.error(f'Failed to get current consumption: {str(e)}')
      raise ValueError(f'Failed to get consumption data: {str(e)}')

  @api_route('/api/consumption/ven/<ven_id>', methods=['GET'])
  def get_ven_consumption(self, ven_id: str):
    """Get consumption data for a specific VEN with totals."""
    try:
      timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
      result = self.consumption_service.get_closest_consumption_point(
        timestamp=timestamp, ven_id=ven_id, resource_id=None
      )

      if not result.success:
        raise ValueError(result.error)

      consumption_data = result.data
      return {
        'ven_id': ven_id,
        'timestamp': timestamp,
        'value': consumption_data['value'],
        'unit': consumption_data['unit'],
        'resource_id': consumption_data['resource_id'],
        'last_updated': datetime.now(timezone.utc).isoformat(),
      }

    except Exception as e:
      logger.error(f'Failed to get VEN consumption: {str(e)}')
      raise ValueError(f'Failed to get VEN consumption data: {str(e)}')

  @api_route('/api/consumption/summary', methods=['GET'])
  def get_consumption_summary(self):
    """Get a summary of all consumption data."""
    try:
      timestamp = int(datetime.now(timezone.utc).timestamp())
      result = self.consumption_service.get_closest_consumption_points(
        target_timestamp=timestamp
      )

      if not result.success:
        raise ValueError(result.error)

      if not result.data.get('consumption_points'):
        raise ValueError('No consumption points found')

      consumption_points = result.data['consumption_points']
      processed_data = self._process_consumption_points(consumption_points)
      print('!!!!processed_data', processed_data)

      # Add additional statistics
      stats_result = self.consumption_service.get_ven_statistics()
      if stats_result.success:
        stats = stats_result.data
        processed_data.update(
          {
            'total_vens': stats['total_vens'],
            'latest_readings': [
              {
                'timestamp': reading.timestamp,
                'value': reading.value,
                'ven_id': reading.ven_id,
                'resource_id': reading.resource_id,
              }
              for reading in stats['latest_readings']
            ],
          }
        )

      return {
        'timestamp': timestamp,
        'total_consumption': processed_data['total_consumption'],
        'unit': processed_data['unit'],
        'ven_count': processed_data['ven_count'],
        'statistics': {
          'total_vens': processed_data.get('total_vens', 0),
          'active_vens': len(processed_data['ven_details']),
          'total_consumption': processed_data['total_consumption'],
        },
      }

    except Exception as e:
      logger.error(f'Failed to get consumption summary: {str(e)}')
      raise ValueError(f'Failed to get consumption summary: {str(e)}')
