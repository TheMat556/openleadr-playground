from src.adr_node.database.database_manager import DatabaseError


class DatabaseConnectionError(DatabaseError):
  """Raised when database connection fails"""

  pass
