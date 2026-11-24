"""Debezium CDC Outbox Relay simulator."""

import json
from datetime import datetime, timezone
from src.db import Database
from src.message_broker import KafkaBroker


class DebeziumCdcRelay:
    def __init__(self, db: Database, broker: KafkaBroker, topic: str = "order-events"):
        self.db = db
        self.broker = broker
        self.topic = topic

    def poll_and_publish(self, batch_size: int = 10) -> int:
        """
        Polls unpublished outbox events, publishes to Kafka, and marks as published.
        Simulates Debezium streaming events from PostgreSQL/MySQL WAL.
        """
        published_count = 0

        with self.db.transaction() as cursor:
            cursor.execute(
                """
                SELECT id, aggregate_type, aggregate_id, event_type, payload, created_at
                FROM outbox_events
                WHERE published_at IS NULL
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (batch_size,),
            )
            rows = cursor.fetchall()

            now_iso = datetime.now(timezone.utc).isoformat()

            for row in rows:
                event_id = row["id"]
                message = {
                    "event_id": event_id,
                    "aggregate_type": row["aggregate_type"],
                    "aggregate_id": row["aggregate_id"],
                    "event_type": row["event_type"],
                    "payload": json.loads(row["payload"]),
                    "timestamp": row["created_at"],
                }

                # Publish to Kafka broker
                self.broker.publish(self.topic, message)

                # Update outbox status to published
                cursor.execute(
                    "UPDATE outbox_events SET published_at = ? WHERE id = ?",
                    (now_iso, event_id),
                )
                published_count += 1

        return published_count
