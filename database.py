"""
Database connection manager and schema initialization using SQLite.
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from config import config


class DatabaseManager:
    """Manages SQLite connection lifecycles and migrations."""

    def __init__(self, db_path: Path = config.DATABASE_PATH):
        self.db_path = db_path
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Ensures the data directory exists prior to connection."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Provides a transactional database connection context."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def initialize_schema(self) -> None:
        """Creates tables if they do not exist."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 1. Recipients Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recipients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone_number TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. Messages Table (Recipient -> Custom Message mapping)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_id INTEGER NOT NULL UNIQUE,
                    message_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recipient_id) REFERENCES recipients (id) ON DELETE CASCADE
                );
            """)

            # 3. Message Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS message_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    provider_message_id TEXT,
                    error_message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (recipient_id) REFERENCES recipients (id) ON DELETE CASCADE
                );
            """)


db = DatabaseManager()