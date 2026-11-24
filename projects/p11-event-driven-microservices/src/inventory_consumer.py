"""Idempotent inventory fulfillment consumer with deduplication table and DLQ."""

from datetime import datetime, timezone
from typing import Any, Dict, List
from src.db import Database
from src.message_broker import KafkaBroker


class InventoryConsumer:
    def __init__(
        self,
        db: Database,
        broker: KafkaBroker,
        consumer_group: str = "inventory-service-group",
        topic: str = "order-events",
        dlq_topic: str = "order-events-dlq",
    ):
        self.db = db
        self.broker = broker
        self.consumer_group = consumer_group
        self.topic = topic
        self.dlq_topic = dlq_topic

    def seed_stock(self, sku: str, quantity: int) -> None:
        with self.db.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO inventory_stock (sku, available_quantity, reserved_quantity)
                VALUES (?, ?, 0)
                ON CONFLICT(sku) DO UPDATE SET available_quantity = excluded.available_quantity
                """,
                (sku, quantity),
            )

    def get_stock(self, sku: str) -> Dict[str, int]:
        with self.db.transaction() as cursor:
            cursor.execute("SELECT available_quantity, reserved_quantity FROM inventory_stock WHERE sku = ?", (sku,))
            row = cursor.fetchone()
            if not row:
                return {"available": 0, "reserved": 0}
            return {"available": row["available_quantity"], "reserved": row["reserved_quantity"]}

    def process_message(self, message: Dict[str, Any]) -> str:
        """
        Idempotently processes a message:
        1. Checks processed_events deduplication table
        2. If duplicate -> returns 'DUPLICATE_SKIPPED'
        3. If new -> allocates inventory and inserts processed_events record in single transaction
        4. If fatal error -> routes message to Dead Letter Queue (DLQ)
        """
        event_id = message.get("event_id")
        if not event_id:
            self.broker.publish(self.dlq_topic, {"error": "Missing event_id", "raw": message})
            return "DLQ"

        now_iso = datetime.now(timezone.utc).isoformat()

        try:
            with self.db.transaction() as cursor:
                # 1. Check if already processed
                cursor.execute(
                    "SELECT 1 FROM processed_events WHERE event_id = ? AND consumer_group = ?",
                    (event_id, self.consumer_group),
                )
                if cursor.fetchone() is not None:
                    return "DUPLICATE_SKIPPED"

                payload = message["payload"]
                sku = payload["sku"]
                qty = payload["quantity"]

                # 2. Allocate inventory
                cursor.execute(
                    "SELECT available_quantity, reserved_quantity FROM inventory_stock WHERE sku = ?",
                    (sku,),
                )
                stock_row = cursor.fetchone()
                if not stock_row:
                    raise ValueError(f"SKU '{sku}' not recognized in inventory.")

                avail = stock_row["available_quantity"]
                if avail < qty:
                    raise ValueError(f"Insufficient stock for {sku}: requested {qty}, available {avail}")

                cursor.execute(
                    """
                    UPDATE inventory_stock
                    SET available_quantity = available_quantity - ?,
                        reserved_quantity = reserved_quantity + ?
                    WHERE sku = ?
                    """,
                    (qty, qty, sku),
                )

                # 3. Mark event as processed
                cursor.execute(
                    "INSERT INTO processed_events (event_id, consumer_group, processed_at) VALUES (?, ?, ?)",
                    (event_id, self.consumer_group, now_iso),
                )

            return "PROCESSED"
        except Exception as e:
            # Route poison pill to DLQ
            self.broker.publish(
                self.dlq_topic,
                {"event_id": event_id, "error": str(e), "message": message},
            )
            return "DLQ"

    def consume_and_process(self, max_messages: int = 10) -> List[str]:
        messages = self.broker.consume(self.topic, self.consumer_group, max_messages)
        return [self.process_message(m) for m in messages]
