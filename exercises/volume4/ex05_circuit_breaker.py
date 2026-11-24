"""
Exercise 4.5: Circuit Breaker State Machine

Problem:
Cascading failures occur when downstream services experience latency or outages.
Implement a CircuitBreaker:
1. State transitions: CLOSED -> OPEN -> HALF-OPEN -> CLOSED.
2. Tracks consecutive failures; when threshold reached, trips to OPEN.
3. In OPEN state, immediately returns fallback response without executing downstream call.
4. After reset_timeout, transitions to HALF-OPEN to probe service health.
"""

import time
from typing import Callable, Literal


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, reset_timeout_sec: float = 0.5):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout_sec
        self.failure_count = 0
        self.state: Literal["CLOSED", "OPEN", "HALF_OPEN"] = "CLOSED"
        self.last_state_change = time.time()

    def call(self, func: Callable[[], str], fallback: Callable[[], str]) -> str:
        now = time.time()

        if self.state == "OPEN":
            if now - self.last_state_change > self.reset_timeout:
                self.state = "HALF_OPEN"
                self.last_state_change = now
            else:
                return fallback()

        try:
            result = func()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
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

    def failing_service():
        raise RuntimeError("Downstream API timeout!")

    def fallback():
        return "CACHED_FALLBACK_PAYLOAD"

    def healthy_service():
        return "LIVE_DATA_PAYLOAD"

    # 1. Initially CLOSED
    assert cb.state == "CLOSED"

    # 2. First failure
    res1 = cb.call(failing_service, fallback)
    assert res1 == "CACHED_FALLBACK_PAYLOAD"
    assert cb.state == "CLOSED"

    # 3. Second failure trips circuit to OPEN
    res2 = cb.call(failing_service, fallback)
    assert cb.state == "OPEN"

    # 4. In OPEN state, function is not even invoked
    res3 = cb.call(failing_service, fallback)
    assert res3 == "CACHED_FALLBACK_PAYLOAD"
    assert cb.state == "OPEN"

    # 5. Wait for reset timeout -> transition to HALF_OPEN -> recover on success
    time.sleep(0.12)
    res4 = cb.call(healthy_service, fallback)
    assert res4 == "LIVE_DATA_PAYLOAD"
    assert cb.state == "CLOSED"

    print("[PASS] Exercise 4.5 verified (Circuit breaker cycled through CLOSED -> OPEN -> HALF_OPEN -> CLOSED).")
