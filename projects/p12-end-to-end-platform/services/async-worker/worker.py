"""Asynchronous background worker consuming fulfillment tasks."""

import json
import os
import sys
import time


def process_fulfillment_task(task_payload: dict) -> bool:
    order_id = task_payload.get("order_id", "unknown")
    print(f"[*] Processing background fulfillment task for Order: {order_id}")
    # Simulates:
    # 1. Deducting physical inventory in Postgres
    # 2. Emitting confirmation notification via email/webhook
    # 3. Invalidating Redis catalog cache
    time.sleep(0.05)
    print(f"[+] Successfully fulfilled Order: {order_id}")
    return True


if __name__ == "__main__":
    print("[*] Async Worker initialized. Ready to process RabbitMQ tasks.")
    # If run in test mode or with mock message
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = process_fulfillment_task({"order_id": "ord_mock_1234"})
        sys.exit(0 if success else 1)
