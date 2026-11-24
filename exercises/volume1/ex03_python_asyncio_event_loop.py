"""
Exercise 1.3: CPython asyncio Cooperative Multitasking and Event Loop Scheduling

Problem:
Design an asynchronous bounded worker pool that:
1. Executes IO-bound tasks concurrently without blocking the main event loop.
2. Uses asyncio.Semaphore to enforce concurrency limits (e.g., max 3 active requests).
3. Handles task timeouts and graceful cancellation without leaving orphaned tasks.
"""

import asyncio
import time
from typing import List


async def worker_task(task_id: int, duration_sec: float, sem: asyncio.Semaphore) -> str:
    async with sem:
        await asyncio.sleep(duration_sec)
        return f"Task-{task_id}: completed in {duration_sec}s"


async def run_worker_pool(total_tasks: int, max_concurrency: int) -> List[str]:
    sem = asyncio.Semaphore(max_concurrency)
    tasks = [
        worker_task(i, 0.05, sem)
        for i in range(total_tasks)
    ]
    return await asyncio.gather(*tasks)


async def test_timeout_and_cancellation():
    async def slow_operation():
        await asyncio.sleep(5.0)
        return "done"

    try:
        await asyncio.wait_for(slow_operation(), timeout=0.1)
        assert False, "Should have timed out"
    except asyncio.TimeoutError:
        pass  # Expected


if __name__ == "__main__":
    print("==> Running Exercise 1.3: asyncio Event Loop & Concurrency...")
    start = time.perf_counter()
    results = asyncio.run(run_worker_pool(total_tasks=6, max_concurrency=3))
    elapsed = time.perf_counter() - start

    assert len(results) == 6
    # 6 tasks with duration 0.05s running with concurrency 3 takes ~0.10s, NOT 0.30s (sequential)
    assert elapsed < 0.25, f"Took {elapsed:.2f}s; concurrency was not properly utilized!"

    asyncio.run(test_timeout_and_cancellation())
    print(f"[PASS] Exercise 1.3 verified (elapsed: {elapsed:.3f}s for 6 tasks).")
