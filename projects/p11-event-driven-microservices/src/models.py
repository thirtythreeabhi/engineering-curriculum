"""Data models for Order, Transactional Outbox, and Inventory systems."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class Order:
    id: str
    customer_id: str
    product_sku: str
    quantity: int
    total_amount: float
    status: str = "PENDING"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class OutboxEvent:
    id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    published_at: Optional[str] = None


@dataclass
class ProcessedEvent:
    event_id: str
    consumer_group: str
    processed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
