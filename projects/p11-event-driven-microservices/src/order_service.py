"""Order service executing Transactional Outbox pattern."""

import json
import uuid
from src.db import Database
from src.models import Order, OutboxEvent


class OrderService:
    def __init__(self, db: Database):
        self.db = db

    def place_order(self, customer_id: str, sku: str, quantity: int, unit_price: float) -> Order:
        """
        Atomically saves the order entity and the corresponding Outbox event
        in a single database transaction. Eliminates dual-write inconsistencies.
        """
        order_id = f"ord_{uuid.uuid4().hex[:8]}"
        event_id = f"evt_{uuid.uuid4().hex[:8]}"
        total_amount = round(quantity * unit_price, 2)

        order = Order(
            id=order_id,
            customer_id=customer_id,
            product_sku=sku,
            quantity=quantity,
            total_amount=total_amount,
            status="CONFIRMED",
        )

        outbox_event = OutboxEvent(
            id=event_id,
            aggregate_type="Order",
            aggregate_id=order_id,
            event_type="OrderCreated",
            payload={
                "order_id": order_id,
                "customer_id": customer_id,
                "sku": sku,
                "quantity": quantity,
                "total_amount": total_amount,
            },
        )

        with self.db.transaction() as cursor:
            # 1. Insert order
            cursor.execute(
                """
                INSERT INTO orders (id, customer_id, product_sku, quantity, total_amount, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (order.id, order.customer_id, order.product_sku, order.quantity, order.total_amount, order.status, order.created_at),
            )

            # 2. Insert outbox event
            cursor.execute(
                """
                INSERT INTO outbox_events (id, aggregate_type, aggregate_id, event_type, payload, created_at, published_at)
                VALUES (?, ?, ?, ?, ?, ?, NULL)
                """,
                (outbox_event.id, outbox_event.aggregate_type, outbox_event.aggregate_id, outbox_event.event_type, json.dumps(outbox_event.payload), outbox_event.created_at),
            )

        return order
