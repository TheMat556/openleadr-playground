import sqlite3
from typing import Dict, List, Any
from pathlib import Path
import threading
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseError(Exception):
  """Custom exception for database-related errors"""

  pass


class DatabaseManager:
  def __init__(self, db_name: str):
    """
    Initialize the database manager with thread-local storage

    Args:
        db_name (str): Name of the database file
    """
    if not db_name or not isinstance(db_name, str):
      raise ValueError('Database name must be a non-empty string')

    self.db_path = (Path('src/openadr_node/database') / db_name).resolve()
    self._local = threading.local()
    self._lock = threading.Lock()

  def _get_connection(self):
    """Get thread-local connection or create new one"""
    if not hasattr(self._local, 'connection') or self._local.connection is None:
      try:
        self._local.connection = sqlite3.connect(self.db_path)
        self._local.cursor = self._local.connection.cursor()
      except sqlite3.Error as e:
        raise DatabaseError(f'Failed to connect to database: {str(e)}')
    return self._local.connection, self._local.cursor

  def connect(self) -> None:
    """Establish thread-local database connection"""
    self._get_connection()

  def disconnect(self) -> None:
    """Close thread-local database connection safely"""
    if hasattr(self._local, 'connection') and self._local.connection:
      self._local.connection.close()
      self._local.connection = None
      self._local.cursor = None

  def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
    """
    Create a new table with thread safety

    Args:
        table_name (str): Name of the table
        columns (Dict[str, str]): Dictionary of column names and their SQL types
    """
    if not table_name or not isinstance(table_name, str):
      raise ValueError('Table name must be a non-empty string')
    if not columns or not isinstance(columns, dict):
      raise ValueError('Columns must be a non-empty dictionary')

    with self._lock:  # Use lock for table creation
      connection, cursor = self._get_connection()
      try:
        cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
        columns_str = ', '.join([f'{col} {dtype}' for col, dtype in columns.items()])
        create_query = f'CREATE TABLE {table_name} ({columns_str})'
        cursor.execute(create_query)
        connection.commit()
      except sqlite3.Error as e:
        raise DatabaseError(f'Failed to create table: {str(e)}')

  def insert_values(
    self, table_name: str, columns: List[str], values: List[Any], replace: bool = False
  ) -> None:
    """
    Insert values with thread safety

    Args:
        table_name (str): Name of the table
        columns (List[str]): List of column names
        values (List[Any]): List of values to insert
        replace (bool): Whether to replace existing values if the key already exists
    """
    if not table_name or not isinstance(table_name, str):
      raise ValueError('Table name must be a non-empty string')
    if not columns or not isinstance(columns, list):
      raise ValueError('Columns must be a list of strings')
    if not values or not isinstance(values, list):
      raise ValueError('Values must be a list')

    connection, cursor = self._get_connection()
    try:
      columns_str = ', '.join(columns)
      placeholders = ', '.join(['?' for _ in values])
      insert_query = f'INSERT {"OR REPLACE INTO"} {table_name} ({columns_str}) VALUES ({placeholders})'
      cursor.execute(insert_query, values)
      connection.commit()
    except sqlite3.Error as e:
      raise DatabaseError(f'Failed to insert values: {str(e)}')
