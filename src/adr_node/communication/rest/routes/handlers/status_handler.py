from datetime import datetime, timezone

from src.adr_node.communication.rest.domain.status_response import StatusResponse
from src.adr_node.communication.rest.routes.decorators.route_decorator import api_route


class StatusHandler:
  """
  Handler for the status-related API endpoint.

  This class provides a method to handle requests for the status of the node.
  """

  startup_time = datetime.now(timezone.utc)

  @api_route('/api/status', methods=['GET'], response_model=StatusResponse)
  def get_status(self):
    """
    Get the current status of the node.

    This method returns the status of the node, including the node ID,
    current status, last updated timestamp, uptime, and version.

    Returns
    -------
    dict
        A dictionary containing the status information of the node.
    """
    current_time = datetime.now(timezone.utc)
    uptime = (current_time - self.startup_time).total_seconds()
    return {
      'node_id': 'node-001',
      'status': 'running',
      'last_updated': current_time,
      'uptime': uptime,
      'version': '0.0.1',
    }
