import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().parent / "app.db"

class Database:
    """Simple SQLite wrapper for project persistence."""

    def __init__(self, db_path: Path = DATABASE_PATH):
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row

    def execute(self, query: str, params: tuple = ()): 
        cursor = self.connection.cursor()
        cursor.execute(query, params)
        self.connection.commit()
        return cursor

    def close(self):
        self.connection.close()
