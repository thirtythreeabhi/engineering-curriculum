"""Database schema and connection manager with transactional support."""

import sqlite3
from contextlib import contextmanager
from typing import Generator


class Database:
    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._conn:
            # Order Service tables
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    customer_id TEXT NOT NULL,
                    product_sku TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    total_amount REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)

            # Transactional Outbox table
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS outbox_events (
                    id TEXT PRIMARY KEY,
                    aggregate_type TEXT NOT NULL,
                    aggregate_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    published_at TEXT
                )
            """)

            # Inventory Service tables
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS inventory_stock (
                    sku TEXT PRIMARY KEY,
                    available_quantity INTEGER NOT NULL,
                    reserved_quantity INTEGER NOT NULL
                )
            """)

            # Idempotent Consumer deduplication table
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_events (
                    event_id TEXT NOT NULL,
                    consumer_group TEXT NOT NULL,
                    processed_at TEXT NOT NULL,
                    PRIMARY KEY (event_id, consumer_group)
                )
            """)

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Provides an atomic ACID transaction boundary."""
        cursor = self._conn.cursor()
        try:
            yield cursor
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        finally:
            cursor.close()

    def close(self) -> None:
        self._conn.close()
