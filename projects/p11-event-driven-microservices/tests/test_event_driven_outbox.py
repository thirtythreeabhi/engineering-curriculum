"""Pytest test suite for Transactional Outbox pattern, CDC, and idempotent consumer."""

import pytest
from src.cdc_relay import DebeziumCdcRelay
from src.db import Database
from src.inventory_consumer import InventoryConsumer
from src.message_broker import KafkaBroker
from src.order_service import OrderService


@pytest.fixture
def test_setup():
    db = Database(":memory:")
    broker = KafkaBroker()
    order_service = OrderService(db)
    cdc_relay = DebeziumCdcRelay(db, broker)
    consumer = InventoryConsumer(db, broker)
    consumer.seed_stock("KEYBOARD-PRO", 50)
    return db, broker, order_service, cdc_relay, consumer


def test_order_creation_atomic_outbox(test_setup):
    db, broker, order_service, cdc_relay, consumer = test_setup

    order = order_service.place_order("cust_42", "KEYBOARD-PRO", 2, 149.99)
    assert order.status == "CONFIRMED"

    # Verify both tables populated atomically
    with db.transaction() as cur:
        cur.execute("SELECT COUNT(*) as c FROM orders WHERE id = ?", (order.id,))
        assert cur.fetchone()["c"] == 1

        cur.execute("SELECT COUNT(*) as c FROM outbox_events WHERE aggregate_id = ?", (order.id,))
        assert cur.fetchone()["c"] == 1


def test_cdc_relay_publishing(test_setup):
    db, broker, order_service, cdc_relay, consumer = test_setup

    order_service.place_order("cust_1", "KEYBOARD-PRO", 1, 149.99)
    order_service.place_order("cust_2", "KEYBOARD-PRO", 3, 149.99)

    # Relay unpublished events to Kafka broker
    published = cdc_relay.poll_and_publish(batch_size=10)
    assert published == 2

    # Broker should now contain 2 messages on order-events topic
    messages = broker.get_all_messages("order-events")
    assert len(messages) == 2
    assert messages[0]["event_type"] == "OrderCreated"

    # Subsequent poll should find 0 pending
    published_second = cdc_relay.poll_and_publish(batch_size=10)
    assert published_second == 0


def test_idempotent_consumer_duplicate_rejection(test_setup):
    db, broker, order_service, cdc_relay, consumer = test_setup

    order_service.place_order("cust_99", "KEYBOARD-PRO", 5, 149.99)
    cdc_relay.poll_and_publish()

    messages = broker.get_all_messages("order-events")
    assert len(messages) == 1
    event_msg = messages[0]

    # First delivery: normal processing
    status_1 = consumer.process_message(event_msg)
    assert status_1 == "PROCESSED"

    stock_after_first = consumer.get_stock("KEYBOARD-PRO")
    assert stock_after_first["available"] == 45
    assert stock_after_first["reserved"] == 5

    # Second delivery (simulating Kafka at-least-once duplicate redelivery)
    status_2 = consumer.process_message(event_msg)
    assert status_2 == "DUPLICATE_SKIPPED"

    # Stock must NOT be decremented again!
    stock_after_second = consumer.get_stock("KEYBOARD-PRO")
    assert stock_after_second["available"] == 45
    assert stock_after_second["reserved"] == 5


def test_dlq_routing_on_insufficient_stock(test_setup):
    db, broker, order_service, cdc_relay, consumer = test_setup

    # Attempt to order 999 units when only 50 exist
    order_service.place_order("cust_whale", "KEYBOARD-PRO", 999, 149.99)
    cdc_relay.poll_and_publish()

    statuses = consumer.consume_and_process()
    assert statuses == ["DLQ"]

    # DLQ topic should contain the failed event
    dlq_messages = broker.get_all_messages("order-events-dlq")
    assert len(dlq_messages) == 1
    assert "Insufficient stock" in dlq_messages[0]["error"]
