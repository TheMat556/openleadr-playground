from src.adr_node.database.exceptions.database_error import DatabaseError


class DatabaseConnectionError(DatabaseError):
  """
  Raised when database connection fails.

  Attributes
  ----------
  message : str
      Error message describing the connection failure.
  """

  def __init__(self, message: str):
    super().__init__(message)
    self.message = message
