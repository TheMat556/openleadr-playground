import os
import sqlite3

class Database:
    """
    A class to represent and manage SQLite database operations for VEN registrations.

    Attributes
    ----------
    db_name : str
        The name of the database file.
    conn : sqlite3.Connection
        The connection object to the SQLite database.

    Methods
    -------
    connect():
        Establishes a connection to the SQLite database.
    create_table():
        Creates the 'vens' table if it doesn't exist.
    insert_ven(ven_name, ven_id=None, registration_id=None):
        Inserts a new VEN entry into the 'vens' table.
    update_ven(ven_name, ven_id, registration_id):
        Updates the ven_id and registration_id for a given ven_name.
    fetch_vens():
        Retrieves all VEN entries from the 'vens' table.
    fetch_ven(ven_id=None, ven_name=None):
        Retrieves a specific VEN entry from the 'vens' table by id or name.
    close():
        Closes the connection to the database.
    """

    def __init__(self, db_name="test.db"):
        self.db_name = db_name
        self.conn = self.connect()
        self.create_table()

    def connect(self):
        """
        Establishes a connection to the SQLite database.

        Returns
        -------
        sqlite3.Connection
            A connection object to the SQLite database.
        """
        return sqlite3.connect(self.db_name)

    def create_table(self):
        """
        Creates the 'vens' table in the database if it does not exist.

        The table has the following columns:
            - id: An integer primary key.
            - name: A text field for the VEN name (not null, unique).
            - ven_id: A text field for the VEN ID (optional).
            - registration_id: A text field for the Registration ID (optional).
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS vens (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    ven_id TEXT,
                    registration_id TEXT
                )
                """
            )

    def insert_ven(self, ven_name, ven_id=None, registration_id=None):
        """
        Inserts a new VEN entry into the 'vens' table.

        Parameters
        ----------
        ven_name : str
            The name of the VEN.
        ven_id : str, optional
            The ID of the VEN (default is None).
        registration_id : str, optional
            The Registration ID of the VEN (default is None).
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO vens (name, ven_id, registration_id)
                VALUES (?, ?, ?)
                """,
                (ven_name, ven_id, registration_id),
            )

    def update_ven(self, ven_name, ven_id, registration_id):
        """
        Updates the ven_id and registration_id for a given ven_name in the 'vens' table.

        Parameters
        ----------
        ven_name : str
            The name of the VEN to update.
        ven_id : str
            The new VEN ID to set.
        registration_id : str
            The new Registration ID to set.
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                UPDATE vens
                SET ven_id = ?, registration_id = ?
                WHERE name = ?
                """,
                (ven_id, registration_id, ven_name),
            )

    def fetch_vens(self):
        """
        Retrieves all VEN entries from the 'vens' table.

        Returns
        -------
        list of tuple
            A list of tuples where each tuple represents a row in the 'vens' table.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM vens")
        return cursor.fetchall()

    def fetch_ven(self, ven_id=None, ven_name=None):
        """
        Retrieves a specific VEN entry from the 'vens' table by id or name.

        Parameters
        ----------
        ven_id : int, optional
            The ID of the VEN to retrieve.
        ven_name : str, optional
            The name of the VEN to retrieve.

        Returns
        -------
        tuple
            A tuple representing the row of the VEN found, or None if no match is found.
        """
        cursor = self.conn.cursor()
        if ven_id is not None:
            cursor.execute("SELECT * FROM vens WHERE ven_id = ?", (ven_id,))
        elif ven_name is not None:
            cursor.execute("SELECT * FROM vens WHERE name = ?", (ven_name,))
        else:
            return None
        return cursor.fetchone()

    def close(self):
        """
        Closes the connection to the SQLite database.
        """
        self.conn.close()