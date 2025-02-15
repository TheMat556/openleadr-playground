class DatabaseError(Exception):
  """
  Base exception for database errors.

  Attributes
  ----------
  message : str
      Error message describing the database error.
  """

  def __init__(self, message: str):
    super().__init__(message)
    self.message = message
