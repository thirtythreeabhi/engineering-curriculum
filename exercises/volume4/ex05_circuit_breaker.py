"""
Exercise 4.5: Circuit Breaker State Machine

Problem:
Cascading failures occur when downstream services experience latency or outages.
Implement a CircuitBreaker:
1. State transitions: CLOSED -> OPEN -> HALF_OPEN -> CLOSED.
2. Tracks CONSECUTIVE failures in CLOSED state (resetting failure_count = 0 on success);
   when threshold is reached, trips to OPEN.
3. In OPEN state, immediately returns fallback response without executing downstream call.
4. After reset_timeout, transitions to HALF_OPEN to probe service health.
"""

import time
from typing import Callable, Literal


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: float = 0.5):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_sec
        self.failure_count = 0
        self.state: Literal["CLOSED", "OPEN", "HALF_OPEN"] = "CLOSED"
        self.last_state_change = time.monotonic()

    def call(self, func: Callable[[], str], fallback: Callable[[], str]) -> str:
        now = time.monotonic()

        if self.state == "OPEN":
            if now - self.last_state_change >= self.reset_timeout:
                self.state = "HALF_OPEN"
                self.last_state_change = now
            else:
                return fallback()

        try:
            result = func()
            # Success in either CLOSED or HALF_OPEN resets consecutive failure counter
            self.failure_count = 0
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.last_state_change = now
            return result
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold or self.state == "HALF_OPEN":
                self.state = "OPEN"
                self.last_state_change = now
            return fallback()


if __name__ == "__main__":
    print("==> Running Exercise 4.5: Circuit Breaker State Machine...")
    cb = CircuitBreaker(failure_threshold=2, reset_timeout_sec=0.1)

    calls = 0

    def failing_service():
        global calls
        calls += 1
        raise RuntimeError("Downstream API timeout!")

    def fallback():
        return "CACHED_FALLBACK_PAYLOAD"

    def healthy_service():
        return "LIVE_DATA_PAYLOAD"

    # 1. Initially CLOSED
    assert cb.state == "CLOSED"

    # 2. Non-consecutive failures separated by success must NOT trip circuit
    assert cb.call(failing_service, fallback) == "CACHED_FALLBACK_PAYLOAD"
    assert cb.state == "CLOSED" and cb.failure_count == 1

    assert cb.call(healthy_service, fallback) == "LIVE_DATA_PAYLOAD"
    assert cb.state == "CLOSED" and cb.failure_count == 0, "Success in CLOSED must reset failure_count!"

    # 3. Now two consecutive failures trip circuit to OPEN
    assert cb.call(failing_service, fallback) == "CACHED_FALLBACK_PAYLOAD"
    assert cb.state == "CLOSED" and cb.failure_count == 1
    assert cb.call(failing_service, fallback) == "CACHED_FALLBACK_PAYLOAD"
    assert cb.state == "OPEN"

    # 4. In OPEN state, downstream function is NOT invoked
    calls_before_open = calls
    assert cb.call(failing_service, fallback) == "CACHED_FALLBACK_PAYLOAD"
    assert calls == calls_before_open, "OPEN circuit must short-circuit without calling downstream!"

    # 5. Wait for reset timeout -> HALF_OPEN probe fails -> immediately back to OPEN
    time.sleep(0.12)
    assert cb.call(failing_service, fallback) == "CACHED_FALLBACK_PAYLOAD"
    assert cb.state == "OPEN"

    # 6. Wait for reset timeout -> HALF_OPEN probe succeeds -> recovers to CLOSED
    time.sleep(0.12)
    assert cb.call(healthy_service, fallback) == "LIVE_DATA_PAYLOAD"
    assert cb.state == "CLOSED" and cb.failure_count == 0

    print("[PASS] Exercise 4.5 verified (Non-consecutive reset + CLOSED -> OPEN -> HALF_OPEN -> CLOSED).")
