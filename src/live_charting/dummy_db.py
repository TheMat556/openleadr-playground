import os
import sqlite3
import random
import asyncio


class DataGenerator:
    def __init__(self, db_name="test_data.db", table_name="data"):
        self.db_name = db_name
        self.table_name = table_name

        db_directory = os.path.dirname(self.db_name)
        os.makedirs(db_directory, exist_ok=True)

        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
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
        self.cursor.execute(
            f"""
            INSERT INTO {self.table_name} (value)
            VALUES (?)
        """,
            (value,),
        )
        self.conn.commit()

    async def generate_data(self, duration=10, interval=1):
        for _ in range(duration):
            value = random.uniform(0, 100)
            self.insert_data(value)
            print(f"Inserted value: {value}")
            await asyncio.sleep(interval)

    def close(self):
        self.conn.close()

    async def generate_interval_data(self):
        await self.generate_data(duration=3600, interval=1)


# Usage
if __name__ == "__main__":
    generator = DataGenerator()

    try:
        asyncio.run(generator.generate_data(duration=3600, interval=1))
    finally:
        generator.close()
