import json
from typing import Dict, Any


class ConsumptionMessageProcessor:
  """
  Processes consumption messages for the MQTTController.
  Keeps parsing/validation logic separate from the controller.
  """

  def __init__(self, ven_id: str):
    self.ven_id = ven_id

  def parse_consumption_message(self, payload: str) -> Dict[str, Any]:
    """
    Parse and return consumption data with ven_id appended.
    Raises:
        json.JSONDecodeError: If payload is not valid JSON.
    """
    data = json.loads(payload)
    data['ven_id'] = self.ven_id
    return data
