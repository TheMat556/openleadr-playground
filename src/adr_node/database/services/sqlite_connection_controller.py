from contextlib import contextmanager
import sqlite3
import threading
from pathlib import Path
from typing import Generator, Tuple

from src.adr_node.database import DatabaseError


class SQLiteConnectionController:
  def __init__(self, db_path: str):
    self.db_path = Path(db_path).resolve()
    self._local = threading.local()
    self._lock = threading.Lock()

  def _ensure_db_exists(self):
    if not self.db_path.exists():
      self.db_path.parent.mkdir(parents=True, exist_ok=True)
      self.db_path.touch()

  @contextmanager
  def get_connection(
    self,
  ) -> Generator[Tuple[sqlite3.Connection, sqlite3.Cursor], None, None]:
    self._ensure_db_exists()

    if not hasattr(self._local, 'connection') or self._local.connection is None:
      try:
        self._local.connection = sqlite3.connect(self.db_path)
        self._local.connection.row_factory = sqlite3.Row
        self._local.cursor = self._local.connection.cursor()
      except sqlite3.Error as e:
        raise DatabaseError(f'Failed to connect to database: {str(e)}')

    try:
      yield self._local.connection, self._local.cursor
    except Exception as e:
      self._local.connection.rollback()
      raise e
    finally:
      self._local.connection.commit()
