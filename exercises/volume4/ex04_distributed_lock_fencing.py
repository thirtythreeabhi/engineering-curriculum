"""
Exercise 4.4: Distributed Locks with Fencing Tokens (Kleppmann Analysis)

Problem:
Standard TTL-based distributed locks (like simple Redis locks) are unsafe under
stop-the-world GC pauses or network delays: Client 1 acquires lock, enters GC pause,
lock TTL expires, Client 2 acquires lock, Client 1 wakes up and commits stale write!

Solution:
1. The lock server enforces active lease ownership and TTL expiration before granting
   the lock to another client (preventing simultaneous dual ownership).
2. Every lock acquisition generates a monotonically increasing Fencing Token.
3. The downstream storage service verifies and rejects writes bearing an older fencing token.
"""

import time
from typing import Optional, Tuple


class FencedLockServer:
    def __init__(self):
        self._current_holder: Optional[str] = None
        self._lease_expires_at: float = 0.0
        self._counter: int = 0

    def acquire(
        self,
        client_id: str,
        ttl_sec: float = 5.0,
        now: Optional[float] = None,
    ) -> Tuple[bool, int]:
        current_time = time.monotonic() if now is None else now

        # Deny acquisition if a different client holds an active, unexpired lease
        if (
            self._current_holder is not None
            and current_time < self._lease_expires_at
            and self._current_holder != client_id
        ):
            return False, 0

        self._current_holder = client_id
        self._lease_expires_at = current_time + ttl_sec
        self._counter += 1
        return True, self._counter

    def release(self, client_id: str) -> bool:
        if self._current_holder == client_id:
            self._current_holder = None
            self._lease_expires_at = 0.0
            return True
        return False


class FencedStorageService:
    def __init__(self):
        self.data: str = ""
        self.highest_fencing_token: int = 0

    def write(self, new_data: str, fencing_token: int) -> bool:
        """
        Only accepts writes if fencing_token > highest_fencing_token seen so far.
        """
        if fencing_token <= self.highest_fencing_token:
            return False  # Stale write rejected!

        self.data = new_data
        self.highest_fencing_token = fencing_token
        return True


if __name__ == "__main__":
    print("==> Running Exercise 4.4: Distributed Lock with Fencing Tokens...")
    lock_server = FencedLockServer()
    storage = FencedStorageService()

    # 1. Client 1 acquires lock at t=10.0 with 5s TTL -> token 1
    acquired_1, token_1 = lock_server.acquire("Client-1", ttl_sec=5.0, now=10.0)
    assert acquired_1 is True and token_1 == 1

    # 2. Contention while lease is active (t=12.0 < 15.0): Client 2 MUST be denied
    acquired_contested, token_contested = lock_server.acquire("Client-2", ttl_sec=5.0, now=12.0)
    assert acquired_contested is False and token_contested == 0, "Contending client must be blocked while lease is active!"

    # 3. Client 1 enters GC pause; at t=16.0 (>= 15.0) lease has expired -> Client 2 acquires token 2
    acquired_2, token_2 = lock_server.acquire("Client-2", ttl_sec=5.0, now=16.0)
    assert acquired_2 is True and token_2 == 2

    # 4. Client 2 executes write with Token 2
    ok_2 = storage.write("Data written by Client 2", token_2)
    assert ok_2 is True
    assert storage.data == "Data written by Client 2"

    # 5. Client 1 wakes up from GC pause and attempts to write with stale Token 1
    ok_1 = storage.write("STALE Data from Client 1", token_1)
    assert ok_1 is False, "Stale write must be rejected by fencing token check!"
    assert storage.data == "Data written by Client 2", "Storage must preserve Client 2 write"

    # 6. Stale Client 1 cannot release Client 2's active lease
    assert lock_server.release("Client-1") is False
    assert lock_server.release("Client-2") is True

    print("[PASS] Exercise 4.4 verified (Lease contention, TTL expiry, and stale fencing token rejection).")
