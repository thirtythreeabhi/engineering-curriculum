"""
Exercise 4.3: Transactional Outbox Pattern and Polling Publisher

Problem:
Implement an atomic outbox publisher that guarantees zero lost messages:
1. Business entity creation and outbox row insertion occur in a single transaction.
2. A polling publisher queries unpublished outbox events.
3. Publishes messages to a message broker with at-least-once delivery semantics.
4. Marks outbox rows as published upon broker acknowledgment.
"""

import sqlite3
import json
import uuid


class OutboxSystem:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self._init_db()
        self.published_broker_messages = []

    def _init_db(self):
        with self.conn:
            self.conn.execute("CREATE TABLE orders (id TEXT PRIMARY KEY, amount REAL)")
            self.conn.execute("""
                CREATE TABLE outbox (
                    id TEXT PRIMARY KEY,
                    event_type TEXT,
                    payload TEXT,
                    published INTEGER DEFAULT 0
                )
            """)

    def create_order(self, order_id: str, amount: float):
        event_id = str(uuid.uuid4())
        payload = json.dumps({"order_id": order_id, "amount": amount})
        with self.conn:
            self.conn.execute("INSERT INTO orders VALUES (?, ?)", (order_id, amount))
            self.conn.execute("INSERT INTO outbox VALUES (?, ?, ?, 0)", (event_id, "OrderCreated", payload))

    def relay_outbox_events(self) -> int:
        cur = self.conn.cursor()
        cur.execute("SELECT id, event_type, payload FROM outbox WHERE published = 0")
        rows = cur.fetchall()

        count = 0
        with self.conn:
            for row in rows:
                # Simulate broker publish
                self.published_broker_messages.append({
                    "id": row["id"],
                    "event_type": row["event_type"],
                    "payload": json.loads(row["payload"]),
                })
                self.conn.execute("UPDATE outbox SET published = 1 WHERE id = ?", (row["id"],))
                count += 1
        return count


if __name__ == "__main__":
    print("==> Running Exercise 4.3: Transactional Outbox Pattern...")
    sys = OutboxSystem()
    sys.create_order("ORD-001", 149.99)
    sys.create_order("ORD-002", 299.50)

    # Initial broker state: empty
    assert len(sys.published_broker_messages) == 0

    # Relay pending outbox events
    relayed = sys.relay_outbox_events()
    assert relayed == 2
    assert len(sys.published_broker_messages) == 2
    assert sys.published_broker_messages[0]["payload"]["order_id"] == "ORD-001"

    # Subsequent relay should find zero pending events
    assert sys.relay_outbox_events() == 0

    print("[PASS] Exercise 4.3 verified (Transactional Outbox events published atomically).")
