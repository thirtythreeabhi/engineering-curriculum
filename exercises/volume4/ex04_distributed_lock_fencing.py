"""
Exercise 4.4: Distributed Locks with Fencing Tokens (Kleppmann Analysis)

Problem:
Standard TTL-based distributed locks (like simple Redis locks) are unsafe under
stop-the-world GC pauses or network delays: Client 1 acquires lock, enters GC pause,
lock TTL expires, Client 2 acquires lock, Client 1 wakes up and commits stale write!

Solution:
Every lock acquisition generates a monotonically increasing Fencing Token.
The downstream storage service verifies and rejects writes bearing an older fencing token.
"""

from typing import Optional, Tuple


class FencedLockServer:
    def __init__(self):
        self._current_holder: Optional[str] = None
        self._counter: int = 0

    def acquire(self, client_id: str) -> Tuple[bool, int]:
        self._current_holder = client_id
        self._counter += 1
        return True, self._counter

    def release(self, client_id: str) -> None:
        if self._current_holder == client_id:
            self._current_holder = None


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

    # Client 1 acquires lock and receives token 1
    _, token_1 = lock_server.acquire("Client-1")
    assert token_1 == 1

    # Client 1 experiences long GC pause... Lock server times out and grants lock to Client 2
    _, token_2 = lock_server.acquire("Client-2")
    assert token_2 == 2

    # Client 2 executes write with Token 2
    ok_2 = storage.write("Data written by Client 2", token_2)
    assert ok_2 is True
    assert storage.data == "Data written by Client 2"

    # Client 1 wakes up from GC pause and attempts to write with stale Token 1
    ok_1 = storage.write("STALE Data from Client 1", token_1)
    assert ok_1 is False, "Stale write must be rejected by fencing token check!"
    assert storage.data == "Data written by Client 2", "Storage must preserve Client 2 write"

    print("[PASS] Exercise 4.4 verified (Stale write prevented by fencing token).")
