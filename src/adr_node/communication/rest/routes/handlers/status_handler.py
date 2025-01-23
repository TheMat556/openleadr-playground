from datetime import datetime

from src.adr_node.communication.rest.domain.status_response import StatusResponse
from src.adr_node.communication.rest.routes.decorators.route_decorator import api_route


class StatusHandler:
  @api_route('/api/status', methods=['GET'], response_model=StatusResponse)
  def get_status(self):
    return {
      'node_id': 'node-001',
      'status': 'running',
      'last_updated': datetime.utcnow(),
      'uptime': 123.45,
      'version': '1.0.0',
    }
