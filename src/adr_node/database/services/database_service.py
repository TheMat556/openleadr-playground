import sqlite3
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.adr_node.database.interfaces.services.idatabase_service import IDatabaseService
from src.openadr_node import logger


class DatabaseError(Exception):
  """Custom exception for database-related errors"""

  pass


class SQLiteDatabaseService(IDatabaseService):
  def __init__(self, db_path: str):
    if not db_path:
      raise ValueError('Database path must be provided')

    self.db_path = (Path('src/openadr_node/database') / db_path).resolve()
    self._local = threading.local()
    self._lock = threading.Lock()
    self._initialize_database()

  def _get_connection(self):
    if not self.db_path.exists():
      self.db_path.parent.mkdir(parents=True, exist_ok=True)
      self.db_path.touch()

    if not hasattr(self._local, 'connection') or self._local.connection is None:
      try:
        self._local.connection = sqlite3.connect(self.db_path)
        self._local.cursor = self._local.connection.cursor()
      except sqlite3.Error as e:
        raise DatabaseError(f'Failed to connect to database: {str(e)}')
    return self._local.connection, self._local.cursor

  def _initialize_database(self) -> None:
    """Initialize all database tables."""
    connection, cursor = self._get_connection()

    tables = {
      'load_profiles': {
        'dstart': 'INTEGER PRIMARY KEY UNIQUE',
        'duration': 'INTEGER NOT NULL',
        'signal_payload': 'FLOAT NOT NULL',
      },
      'consumption': {
        'timestamp': 'INTEGER PRIMARY KEY',
        'ven_id': 'TEXT NOT NULL',
        'resource_id': 'TEXT NOT NULL',
        'value': 'FLOAT NOT NULL',
      },
      'z_values': {
        'timestamp': 'INTEGER NOT NULL',
        'ven_id': 'TEXT NOT NULL',
        'z_value': 'FLOAT NOT NULL',
        'PRIMARY KEY': '(timestamp, ven_id)',
      },
    }

    for table_name, columns in tables.items():
      try:
        columns_str = ', '.join([f'{col} {dtype}' for col, dtype in columns.items()])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})')
      except sqlite3.Error as e:
        logger.error(f'Failed to create table {table_name}: {str(e)}')
        raise DatabaseError(f'Failed to create table {table_name}: {str(e)}')

    connection.commit()

  def execute_query(
    self, query: str, params: Optional[List[Any]] = None
  ) -> List[Dict[str, Any]]:
    connection, cursor = self._get_connection()
    try:
      cursor.execute(query, params or [])
      if query.strip().upper().startswith('SELECT'):
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
      else:
        connection.commit()
        return []
    except sqlite3.Error as e:
      logger.error(f'Query execution failed: {str(e)}')
      raise DatabaseError(f'Query execution failed: {str(e)}')

  def execute_batch(self, query: str, batch_values: List[List[Any]]) -> None:
    connection, cursor = self._get_connection()
    try:
      cursor.executemany(query, batch_values)
      connection.commit()
    except sqlite3.Error as e:
      logger.error(f'Batch operation failed: {str(e)}')
      raise DatabaseError(f'Batch operation failed: {str(e)}')
