import sqlite3
import time
import random


class DataGenerator:
  """
  A class to generate and store dummy data in an SQLite database.

  Attributes
  ----------
  db_name : str
      The name of the SQLite database file.
  table_name : str
      The name of the table where data will be stored.
  conn : sqlite3.Connection
      The SQLite database connection object.
  cursor : sqlite3.Cursor
      The SQLite cursor object for executing SQL commands.

  Methods
  -------
  _create_table()
      Creates a table for storing dummy data if it doesn't already exist.
  insert_data(value)
      Inserts a single value into the table.
  generate_data(duration=10, interval=1)
      Generates dummy data for a specified duration, inserting a new value at each interval.
  close()
      Closes the database connection.
  """

  def __init__(self, db_name='test_data.db', table_name='data'):
    """
    Initializes the DataGenerator with a specified database and table name.

    Parameters
    ----------
    db_name : str, optional
        The name of the SQLite database file (default is "test_data.db").
    table_name : str, optional
        The name of the table where data will be stored (default is "data").
    """
    self.db_name = db_name
    self.table_name = table_name
    self.conn = sqlite3.connect(self.db_name)
    self.cursor = self.conn.cursor()
    self._create_table()

  def _create_table(self):
    """
    Creates a table for storing dummy data if it doesn't already exist.

    The table schema includes an auto-incrementing primary key, a timestamp, and a value.
    """
    self.cursor.execute(
      f"""
            CREATE TABLE IF NOT EXISTS {self.table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                value REAL
            )
        """
    )
    self.conn.commit()

  def insert_data(self, value):
    """
    Inserts a single value into the table.

    Parameters
    ----------
    value : float
        The value to be inserted into the table.
    """
    self.cursor.execute(
      f"""
            INSERT INTO {self.table_name} (value)
            VALUES (?)
        """,
      (value,),
    )
    self.conn.commit()

  def generate_data(self, duration=10, interval=1):
    """
    Generates dummy data for a specified duration, inserting a new value at each interval.

    Parameters
    ----------
    duration : int, optional
        The total duration for which to generate data (in seconds, default is 10).
    interval : int, optional
        The interval between data insertions (in seconds, default is 1).
    """
    for _ in range(duration):
      value = random.uniform(0, 100)  # Generate a random float value between 0 and 100
      self.insert_data(value)
      print(f'Inserted value: {value}')
      time.sleep(interval)

  def close(self):
    """
    Closes the database connection.
    """
    self.conn.close()


# Usage
if __name__ == '__main__':
  generator = DataGenerator()
  try:
    generator.generate_data(
      duration=3600, interval=1
    )  # Generate data for 3600 seconds (1 hour), inserting a value every second
  finally:
    generator.close()
