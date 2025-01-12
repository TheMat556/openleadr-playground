import sqlite3
from typing import Dict, List, Any
from pathlib import Path
import threading

from src.openadr_node import logger


class DatabaseError(Exception):
  """Custom exception for database-related errors"""

  pass


class DatabaseManager:
  """
  Manages SQLite database connections and operations with thread safety.

  Attributes:
      db_path (Path): Path to the SQLite database file.
      _local (threading.local): Thread-local storage for database connections.
      _lock (threading.Lock): Lock for thread-safe operations.
  """

  def __init__(self, db_name: str):
    """
    Initialize the database manager with thread-local storage.

    Args:
        db_name (str): Name of the database file.
    """
    if not db_name or not isinstance(db_name, str):
      raise ValueError('Database name must be a non-empty string')

    self.db_path = (Path('src/openadr_node/database') / db_name).resolve()
    self._local = threading.local()
    self._lock = threading.Lock()

  def _get_connection(self):
    """Get thread-local connection or create a new one."""
    if not hasattr(self._local, 'connection') or self._local.connection is None:
      try:
        self._local.connection = sqlite3.connect(self.db_path)
        self._local.cursor = self._local.connection.cursor()
      except sqlite3.Error as e:
        raise DatabaseError(f'Failed to connect to database: {str(e)}')
    return self._local.connection, self._local.cursor

  def connect(self) -> None:
    """Establish thread-local database connection."""
    self._get_connection()

  def disconnect(self) -> None:
    """Close thread-local database connection safely."""
    if hasattr(self._local, 'connection') and self._local.connection:
      self._local.connection.close()
      self._local.connection = None
      self._local.cursor = None

  def create_table(self, table_name: str, columns: Dict[str, str]) -> None:
    """
    Create a new table with thread safety.

    Args:
        table_name (str): Name of the table.
        columns (Dict[str, str]): Dictionary of column names and their SQL types.
    """
    if not table_name or not isinstance(table_name, str):
      raise ValueError('Table name must be a non-empty string')
    if not columns or not isinstance(columns, dict):
      raise ValueError('Columns must be a non-empty dictionary')

    with self._lock:
      connection, cursor = self._get_connection()
      try:
        cursor.execute(f'DROP TABLE IF EXISTS {table_name}')
        columns_str = ', '.join([f'{col} {dtype}' for col, dtype in columns.items()])
        create_query = f'CREATE TABLE {table_name} ({columns_str})'
        cursor.execute(create_query)
        connection.commit()
      except sqlite3.Error as e:
        raise DatabaseError(f'Failed to create table: {str(e)}')

  @staticmethod
  def _validate_input(table_name: str, columns: List[str], values: List[Any]) -> None:
    """Validate basic input parameters."""
    if not table_name or not isinstance(table_name, str):
      raise ValueError('Table name must be a non-empty string')
    if not columns or not isinstance(columns, list):
      raise ValueError('Columns must be a list of strings')
    if not values or not isinstance(values, list):
      raise ValueError('Values must be a list')
    if len(columns) != len(values):
      raise ValueError(
        f'Number of columns ({len(columns)}) must match number of values ({len(values)})'
      )

  def _validate_table_and_columns(self, table_name: str, columns: List[str]) -> None:
    """Validate table exists and columns are valid."""
    connection, cursor = self._get_connection()

    # Check table exists
    cursor.execute(
      "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,)
    )
    if not cursor.fetchone():
      raise DatabaseError(f'Table {table_name} does not exist')

    # Check columns exist
    cursor.execute(f'PRAGMA table_info({table_name})')
    valid_columns = {row[1] for row in cursor.fetchall()}
    invalid_columns = set(columns) - valid_columns
    if invalid_columns:
      raise DatabaseError(f'Invalid columns for table {table_name}: {invalid_columns}')

  @staticmethod
  def _build_insert_query(table_name: str, columns: List[str], replace: bool) -> str:
    """Build the INSERT query with proper quoting."""
    columns_str = ', '.join(f'"{col}"' for col in columns)
    placeholders = ', '.join(['?' for _ in columns])
    query = 'INSERT OR REPLACE' if replace else 'INSERT'
    return f'{query} INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'

  def insert_values(
    self, table_name: str, columns: List[str], values: List[Any], replace: bool = False
  ) -> None:
    """
    Insert values with thread safety.

    Args:
        table_name (str): Name of the table.
        columns (List[str]): List of column names.
        values (List[Any]): List of values to insert.
        replace (bool): Whether to replace existing values if the key already exists.
    """
    # Validate inputs
    self._validate_input(table_name, columns, values)

    with self._lock:
      # Validate table and columns
      self._validate_table_and_columns(table_name, columns)

      # Execute insert
      connection, cursor = self._get_connection()
      try:
        insert_query = self._build_insert_query(table_name, columns, replace)
        logger.debug(f'Executing query: {insert_query} with values: {values}')

        cursor.execute(insert_query, values)
        connection.commit()
      except sqlite3.Error as e:
        error_msg = f'Failed to insert values into {table_name}: {str(e)}'
        logger.error(error_msg)
        raise DatabaseError(error_msg)

  def insert_values_batch(
    self,
    table_name: str,
    columns: List[str],
    batch_values: List[List[Any]],
    conflict_cols: List[str],
  ) -> None:
    """
    Perform batch upsert based on a unique set of columns (conflict_cols).
    If rows with the same conflict columns exist, they will be updated;
    otherwise, new rows are inserted.

    Args:
        table_name (str): Name of the table.
        columns (List[str]): List of column names.
        batch_values (List[List[Any]]): List of value lists to insert.
        conflict_cols (List[str]): Columns used for the ON CONFLICT clause (e.g. ["timestamp", "ven_id"]).
    """
    # Validate that conflict_cols is not empty
    if not conflict_cols:
      raise ValueError('You must specify at least one conflict column.')

    # Validate table and columns
    self._validate_table_and_columns(table_name, columns)

    # Build comma-separated column names and placeholders
    columns_str = ', '.join(f'"{col}"' for col in columns)
    placeholders = ', '.join(['?' for _ in columns])

    # Build the conflict clause, e.g. ON CONFLICT("timestamp","ven_id")
    conflict_clause = ', '.join(f'"{col}"' for col in conflict_cols)

    # Skip the conflict columns in the update portion
    update_assignments = ', '.join(
      f'"{col}" = EXCLUDED."{col}"' for col in columns if col not in conflict_cols
    )

    # Final upsert query
    upsert_query = f"""
            INSERT INTO "{table_name}" ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT({conflict_clause}) DO UPDATE
            SET {update_assignments}
        """

    connection, cursor = self._get_connection()

    with self._lock:
      try:
        # Executemany to handle all rows in batch_values
        cursor.executemany(upsert_query, batch_values)
        connection.commit()
      except sqlite3.Error as e:
        error_msg = f'Failed to upsert rows into "{table_name}" using columns {conflict_cols}: {str(e)}'
        logger.error(error_msg)
        raise DatabaseError(error_msg)

  def execute_query(self, query: str, params: List[Any] = []) -> List[Dict[str, Any]]:
    """
    Execute a query and return the results.

    Args:
        query (str): The SQL query to execute.
        params (List[Any]): List of parameters to safely include in the query.

    Returns:
        List[Dict[str, Any]]: The query results as a list of dictionaries.
    """
    connection, cursor = self._get_connection()
    try:
      cursor.execute(query, tuple(params))
      rows = cursor.fetchall()
      columns = [desc[0] for desc in cursor.description]
      return [dict(zip(columns, row)) for row in rows]
    except sqlite3.Error as e:
      raise DatabaseError(f'Failed to execute query: {str(e)}')
