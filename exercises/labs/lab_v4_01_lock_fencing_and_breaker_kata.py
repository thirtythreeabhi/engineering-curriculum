"""
Lab V4-01 (Volume 4 Ch 7 & Ch 9 - Distributed Locking & Reliability):
Lock Lease Contention & Circuit Breaker Reset Debugging Kata

Instructions:
This lab reproduces two subtle distributed-systems bugs:
  1. Part A (`BrokenFencedLockServer.acquire`): Blindly overwrites `_current_holder`
     even while another client holds an active, unexpired lease!
  2. Part B (`BrokenCircuitBreaker.call`): Never resets `failure_count = 0` on
     success in `CLOSED` state, causing isolated errors hours apart to trip the breaker!

Your task:
- Fix the `BUG` in `BrokenFencedLockServer.acquire()` to enforce active lease + TTL check.
- Fix the `BUG` in `BrokenCircuitBreaker.call()` to reset `failure_count = 0` on success.

Run this file directly to check your fixes:
    python3 exercises/labs/lab_v4_01_lock_fencing_and_breaker_kata.py

Reference solutions:
- exercises/volume4/ex04_distributed_lock_fencing.py
- exercises/volume4/ex05_circuit_breaker.py
"""

import time
from typing import Callable, Literal, Optional, Tuple


class BrokenFencedLockServer:
    def __init__(self):
        self._current_holder: Optional[str] = None
        self._lease_expires_at: float = 0.0
        self._counter: int = 0

    def acquire(self, client_id: str, ttl_sec: float = 5.0, now: float = 0.0) -> Tuple[bool, int]:
        # BUG: Missing check for active lease ownership & TTL expiration!
        # TODO: If _current_holder is set, now < _lease_expires_at, and _current_holder != client_id,
        #       return (False, 0).
        self._current_holder = client_id
        self._lease_expires_at = now + ttl_sec
        self._counter += 1
        return True, self._counter


class BrokenCircuitBreaker:
    def __init__(self, failure_threshold: int = 2, reset_timeout_sec: float = 0.1):
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
            res = func()
            # BUG: Only resets failure_count when transitioning out of HALF_OPEN!
            # TODO: Reset `self.failure_count = 0` on EVERY success (including CLOSED state).
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
                self.last_state_change = now
            return res
        except Exception:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold or self.state == "HALF_OPEN":
                self.state = "OPEN"
                self.last_state_change = now
            return fallback()


if __name__ == "__main__":
    print("==> Running Lab V4-01: Lock Fencing & Circuit Breaker Kata...")

    # Verify Part A: Lock lease contention & expiry
    lock = BrokenFencedLockServer()
    ok1, tok1 = lock.acquire("client-1", ttl_sec=5.0, now=10.0)
    assert ok1 is True and tok1 == 1

    ok_contested, tok_contested = lock.acquire("client-2", ttl_sec=5.0, now=12.0)
    assert ok_contested is False and tok_contested == 0, (
        "[FAIL Part A] Contending client stole active unexpired lease!"
    )

    ok2, tok2 = lock.acquire("client-2", ttl_sec=5.0, now=16.0)
    assert ok2 is True and tok2 == 2

    # Verify Part B: Non-consecutive failures separated by success must NOT open breaker
    cb = BrokenCircuitBreaker(failure_threshold=2, reset_timeout_sec=0.1)
    fail = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    ok = lambda: "OK"
    fb = lambda: "FALLBACK"

    assert cb.call(fail, fb) == "FALLBACK"
    assert cb.call(ok, fb) == "OK"
    assert cb.call(fail, fb) == "FALLBACK"
    assert cb.state == "CLOSED", (
        "[FAIL Part B] Non-consecutive failures tripped breaker because success did not reset failure_count!"
    )

    print("[PASS] Lab V4-01 completed!")
