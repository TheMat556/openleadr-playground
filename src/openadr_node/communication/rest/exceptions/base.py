from datetime import datetime


class OpenADRBaseException(Exception):
  """Base exception for all OpenADR exceptions"""

  def __init__(self, message: str):
    self.message = message
    self.timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    self.user = 'TheMat556'
    super().__init__(self.message)

  def to_dict(self):
    return {
      'message': self.message,
      'timestamp': self.timestamp,
      'user': self.user,
      'error_type': self.__class__.__name__,
    }
