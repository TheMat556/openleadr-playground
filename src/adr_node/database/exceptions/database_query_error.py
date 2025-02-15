from src.adr_node.database.exceptions.database_error import DatabaseError


class DatabaseQueryError(DatabaseError):
  """
  Raised when database query fails.

  Attributes
  ----------
  message : str
      Error message describing the query failure.
  """

  def __init__(self, message: str):
    super().__init__(message)
    self.message = message
