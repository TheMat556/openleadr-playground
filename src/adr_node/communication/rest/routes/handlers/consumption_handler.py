from datetime import datetime, timezone
from typing import Dict, Any, List

import logging

from src.adr_node.communication.rest.routes.decorators.route_decorator import api_route


class ConsumptionHandler:
  """
  Handler for consumption-related API endpoints.

  This class provides methods to handle requests for consumption data,
  including current consumption, consumption by VEN, and consumption summary.
  """

  def __init__(self, consumption_service):
    self.consumption_service = consumption_service

  @staticmethod
  def _process_consumption_points(points: List[Any]) -> Dict[str, Any]:
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
    """
    Get current consumption data for all VENs with detailed statistics.

    Returns:
        JSON response containing current consumption data
    """
    try:
      timestamp = int(datetime.now(timezone.utc).timestamp())
      consumption_result = self.consumption_service.get_current_consumption()

      if not consumption_result.success:
        raise ValueError(consumption_result.error or 'Failed to get consumption data')

      # Extract all relevant data from the service result
      data = consumption_result.data
      response = {
        'timestamp': timestamp,
        'total_consumption': data.get('total_consumption', 0.0),
        'average_consumption': data.get('average_consumption', 0.0),
        'measurement_unit': data.get('unit', 'kWh'),
        'statistics': {
          'point_count': data.get('point_count', 0),
          'time_window': {
            'start': data.get('timestamp_range', {}).get('start'),
            'end': data.get('timestamp_range', {}).get('end'),
            'window_ms': data.get('timestamp_range', {}).get('window_ms'),
          },
        },
      }

      return response

    except Exception as e:
      logging.error(f'Failed to get current consumption: {str(e)}')
      raise ValueError(f'Failed to retrieve consumption data: {str(e)}')

  @api_route('/api/consumption/ven/<ven_id>', methods=['GET'])
  def get_ven_consumption(self, ven_id: str):
    """
    Get consumption data for a specific VEN with totals.

    Args:
        ven_id: The ID of the VEN

    Returns:
        JSON response containing consumption data for the specified VEN
    """
    try:
      timestamp = int(datetime.now(timezone.utc).timestamp())
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
      logging.error(f'Failed to get VEN consumption: {str(e)}')
      raise ValueError(f'Failed to get VEN consumption data: {str(e)}')

  @api_route('/api/consumption/summary', methods=['GET'])
  def get_consumption_summary(self):
    """
    Get a summary of all consumption data.

    Returns:
        JSON response containing a summary of all consumption data
    """
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
      logging.error(f'Failed to get consumption summary: {str(e)}')
      raise ValueError(f'Failed to get consumption summary: {str(e)}')
