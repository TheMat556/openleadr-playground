import sqlite3

from src.adr_node.database.services.domains.table_schema import TableSchema
from src.adr_node.database.services.sqlite_connection_controller import (
  SQLiteConnectionController,
)


class SchemaController:
  SCHEMAS = {
    'load_profiles': TableSchema(
      name='load_profiles',
      columns={
        'dstart': 'INTEGER PRIMARY KEY UNIQUE',
        'duration': 'INTEGER NOT NULL',
        'signal_payload': 'FLOAT NOT NULL',
      },
      indexes={
        'idx_load_profiles_dstart': 'CREATE INDEX IF NOT EXISTS idx_load_profiles_dstart ON load_profiles(dstart)'
      },
    ),
    'consumption': TableSchema(
      name='consumption',
      columns={
        'timestamp': 'INTEGER PRIMARY KEY',
        'ven_id': 'TEXT NOT NULL',
        'resource_id': 'TEXT NOT NULL',
        'value': 'FLOAT NOT NULL',
      },
      indexes={
        'idx_consumption_ven': 'CREATE INDEX IF NOT EXISTS idx_consumption_ven ON consumption(ven_id)',
        'idx_consumption_timestamp': 'CREATE INDEX IF NOT EXISTS idx_consumption_timestamp ON consumption(timestamp)',
      },
    ),
    'z_values': TableSchema(
      name='z_values',
      columns={
        'timestamp': 'INTEGER NOT NULL',
        'ven_id': 'TEXT NOT NULL',
        'z_value': 'FLOAT NOT NULL',
        'PRIMARY KEY': '(timestamp, ven_id)',
      },
      indexes={
        'idx_z_values_timestamp': 'CREATE INDEX IF NOT EXISTS idx_z_values_timestamp ON z_values(timestamp)'
      },
    ),
  }

  def __init__(self, connection_manager: SQLiteConnectionController):
    self.connection_manager = connection_manager

  def initialize_schema(self):
    with self.connection_manager.get_connection() as (conn, cursor):
      for schema in self.SCHEMAS.values():
        self._create_table(cursor, schema)
        self._create_indexes(cursor, schema)

  def _create_table(self, cursor: sqlite3.Cursor, schema: TableSchema):
    columns_str = ', '.join([f'{col} {dtype}' for col, dtype in schema.columns.items()])
    create_table_sql = f'CREATE TABLE IF NOT EXISTS {schema.name} ({columns_str})'
    cursor.execute(create_table_sql)

  def _create_indexes(self, cursor: sqlite3.Cursor, schema: TableSchema):
    if schema.indexes:
      for index_sql in schema.indexes.values():
        cursor.execute(index_sql)
