class DatabaseError(Exception):
  """Base exception for database errors"""

  pass


class DatabaseConnectionError(DatabaseError):
  """Raised when database connection fails"""

  pass


class DatabaseQueryError(DatabaseError):
  """Raised when database query fails"""

  pass
