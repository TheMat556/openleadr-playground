from src.adr_node.communication.rest.routes.decorators.route_decorator import api_route


class LoadProfileHandler:
  def __init__(self, load_profile_service):
    self.load_profile_service = load_profile_service

  @api_route('/api/load-profile', methods=['GET'])
  def get_load_profile(self):
    # Implementation here
    pass
