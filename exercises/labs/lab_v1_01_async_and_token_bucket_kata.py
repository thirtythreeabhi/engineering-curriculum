"""
Lab V1-01 (Volumes 1 Ch 2, Ch 5, Ch 7):
Async Event-Loop Blocking & Token Bucket Starvation Debugging Kata

Instructions:
This lab contains TWO classic backend reliability bugs found in AI-generated code:
  1. Part A (`run_bounded_batch`): Calls blocking `time.sleep()` inside an `async def`
     coroutine instead of yielding to the asyncio event loop (`await asyncio.sleep()`).
  2. Part B (`TokenBucket.allow`): Advances `last_refill` even when a request is DENIED,
     without saving the newly refilled fractional tokens (or drops them), starving
     clients who retry slightly faster than the refill rate.

Your task:
- Fix the `BUG` in Part A so 6 concurrent tasks with max_concurrency=3 finish in ~0.10s.
- Fix the `BUG` / `TODO` in Part B so fractional token refills are preserved across
  denied requests and steady-rate clients are NOT starved.

Run this file directly to check your fixes:
    python3 exercises/labs/lab_v1_01_async_and_token_bucket_kata.py

Reference solutions:
- exercises/volume1/ex03_python_asyncio_event_loop.py
"""

import asyncio
import time
from typing import List


# ==============================================================================
# PART A: Fix the Event-Loop Blocking Bug
# ==============================================================================
async def fetch_item(item_id: int, sem: asyncio.Semaphore) -> str:
    async with sem:
        # BUG: Blocking the entire event-loop thread! All coroutines serialize!
        # TODO: Replace with non-blocking asyncio sleep for 0.05s.
        time.sleep(0.05)
        return f"item-{item_id}"


async def run_bounded_batch(total_items: int, max_concurrency: int) -> List[str]:
    sem = asyncio.Semaphore(max_concurrency)
    return await asyncio.gather(*(fetch_item(i, sem) for i in range(total_items)))


# ==============================================================================
# PART B: Fix the Token Bucket Starvation Bug (cf. Redis Lua Token Bucket)
# ==============================================================================
class TokenBucket:
    def __init__(self, capacity: float, refill_rate_per_sec: float, now: float = 0.0):
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.tokens = capacity
        self.last_refill = now

    def allow(self, cost: float = 1.0, now: float = 0.0) -> bool:
        elapsed = max(0.0, now - self.last_refill)
        refilled = min(self.capacity, self.tokens + elapsed * self.refill_rate)

        if refilled >= cost:
            self.tokens = refilled - cost
            self.last_refill = now
            return True

        # BUG: Advancing last_refill without persisting `refilled` discards all
        # fractional tokens accumulated since the last allowed request!
        # Clients retrying every 0.4s for a 1.0s refill rate will starve forever!
        # TODO: Persist `self.tokens = refilled` AND update `self.last_refill = now`
        # (or leave both untouched on denial if not persisting `refilled`).
        self.last_refill = now
        return False


if __name__ == "__main__":
    print("==> Running Lab V1-01: Async Event-Loop & Token Bucket Kata...")

    # Verify Part A
    start = time.perf_counter()
    results = asyncio.run(run_bounded_batch(total_items=6, max_concurrency=3))
    elapsed = time.perf_counter() - start
    assert len(results) == 6
    assert elapsed < 0.22, (
        f"[FAIL Part A] Took {elapsed:.3f}s (expected ~0.10s). "
        "Did you replace blocking time.sleep() with await asyncio.sleep()?"
    )

    # Verify Part B: capacity=1, refill=1 token/sec
    bucket = TokenBucket(capacity=1.0, refill_rate_per_sec=1.0, now=0.0)
    assert bucket.allow(cost=1.0, now=0.0) is True   # Consumes initial token -> 0.0 left
    assert bucket.allow(cost=1.0, now=0.4) is False  # 0.4 tokens accrued (< 1.0) -> denied
    assert bucket.allow(cost=1.0, now=0.8) is False  # 0.8 tokens accrued (< 1.0) -> denied
    # By t=1.1s, 1.1 tokens total have accrued since t=0.0 -> MUST be allowed!
    assert bucket.allow(cost=1.0, now=1.1) is True, (
        "[FAIL Part B] Client starved! Fractional tokens accrued before denials were lost."
    )

    print("[PASS] Lab V1-01 completed!")
