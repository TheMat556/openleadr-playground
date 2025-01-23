import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Any, Dict

from src.adr_node.database.interfaces.services.idatabase_service import IDatabaseService
from src.adr_node.database.services.schema.schema_controller import SchemaController
from src.adr_node.database.services.base.sqlite_connection_controller import (
  SQLiteConnectionController,
)
from src.openadr_node import logger
from src.openadr_node.database.database_manager import DatabaseError


class SQLiteDatabaseService(IDatabaseService):
  def __init__(self, db_path: str):
    if not db_path:
      raise ValueError('Database path must be provided')

    self.connection_manager = SQLiteConnectionController(db_path)
    self.schema_manager = SchemaController(self.connection_manager)
    self._initialize_database()

  def _initialize_database(self) -> None:
    """Initialize all database tables and indexes."""
    self.schema_manager.initialize_schema()

  @contextmanager
  def transaction(self):
    """Context manager for handling transactions."""
    with self.connection_manager.get_connection() as (conn, cursor):
      try:
        yield cursor
        conn.commit()
      except Exception:
        conn.rollback()
        raise

  def execute_query(
    self, query: str, params: Optional[List[Any]] = None
  ) -> List[Dict[str, Any]]:
    with self.connection_manager.get_connection() as (_, cursor):
      try:
        cursor.execute(query, params or [])
        if query.strip().upper().startswith('SELECT'):
          return [dict(row) for row in cursor.fetchall()]
        return []
      except sqlite3.Error as e:
        logger.error(f'Query execution failed: {str(e)}')
        raise DatabaseError(f'Query execution failed: {str(e)}')

  def execute_batch(self, query: str, batch_values: List[List[Any]]) -> None:
    with self.connection_manager.get_connection() as (conn, cursor):
      try:
        cursor.executemany(query, batch_values)
      except sqlite3.Error as e:
        logger.error(f'Batch operation failed: {str(e)}')
        raise DatabaseError(f'Batch operation failed: {str(e)}')
