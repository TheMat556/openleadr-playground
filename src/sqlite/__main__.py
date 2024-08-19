# src/sqlite/__main__.py

from .sqlite import Database

# Example usage
def main():
    db_path = "./database/openleadr.db"
    db = Database(db_path)

    if not db.fetch_ven(ven_name="ven123"):
        db.create_table()
        db.insert_ven("ven123")

        db.update_ven("ven123", "VEN_ID_001", "REG_ID_001")

    print("Database initialized.")
    db.close()


if __name__ == "__main__":
    main()