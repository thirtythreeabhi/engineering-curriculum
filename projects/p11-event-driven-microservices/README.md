# Project 11: Event-Driven Microservices with Transactional Outbox Pattern & CDC

Distributed order and inventory fulfillment system eliminating distributed dual-write inconsistencies using the Transactional Outbox pattern, Debezium Change Data Capture (CDC) streaming to Apache Kafka, and idempotent message consumption with a dedicated deduplication log and Dead Letter Queue (DLQ).

## Distributed Systems Problem & Solution

1. **The Dual-Write Failure Mode**:
   - In standard microservices, saving an entity in a relational database and publishing an event to a message broker (Kafka/RabbitMQ) cannot be done atomically without 2PC (Two-Phase Commit, which introduces latency and coordinator lockups).
   - If the database commits but the network to Kafka drops, the message is lost forever.
   - If the event is sent first but the database rollback occurs, downstream services process a ghost order.

2. **The Transactional Outbox Solution**:
   - The Order Service saves the `orders` row AND the `outbox_events` record in a single local database transaction.
   - An independent Change Data Capture (CDC) relay (modeled after Debezium) tails the database transaction log, extracts unpublished events, delivers them to Kafka topics (`order-events`), and flags them as published.

3. **Idempotent Consumer Pattern**:
   - Because message brokers guarantee at-least-once delivery, consumers must handle duplicate deliveries gracefully.
   - The Inventory Consumer checks an atomic `processed_events` table before applying state updates. Duplicate deliveries are identified and skipped without duplicate inventory deductions.

4. **Dead Letter Queue (DLQ)**:
   - Poison pills or fatal domain exceptions (e.g., zero available stock) route to `order-events-dlq` to prevent poison message blocking.

## Directory Structure

```
p11-event-driven-microservices/
├── README.md
├── requirements.txt
├── src/
│   ├── cdc_relay.py
│   ├── db.py
│   ├── inventory_consumer.py
│   ├── message_broker.py
│   ├── models.py
│   └── order_service.py
└── tests/
    └── test_event_driven_outbox.py
```

## Running the Pytest Suite

```bash
PYTHONPATH=. pytest tests/ -v
```
