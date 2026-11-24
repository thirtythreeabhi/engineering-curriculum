"""
Exercise 4.1: Vector Clocks and Distributed Causality

Problem:
Physical clocks drift due to network skew and oscillator variance (NTP clock drift).
Vector Clocks track causal relationships across distributed processes without relying
on physical wall-clock synchronization.

Implement a VectorClock:
1. tick(): increments local process counter.
2. send_message(): returns a snapshot of current vector clock.
3. receive_message(remote_clock): merges local clock with incoming clock:
   V_local[i] = max(V_local[i], V_remote[i]) for all i, then ticks local counter.
4. compare(clock_A, clock_B): determines if A happens-before B (A -> B), B happens-before A,
   or if they are concurrent / conflicting (A || B).
"""

from typing import Dict, Literal


class VectorClock:
    def __init__(self, node_id: str, all_nodes: list[str]):
        self.node_id = node_id
        self.clock: Dict[str, int] = {nid: 0 for nid in all_nodes}

    def tick(self) -> Dict[str, int]:
        self.clock[self.node_id] += 1
        return dict(self.clock)

    def send_event(self) -> Dict[str, int]:
        self.clock[self.node_id] += 1
        return dict(self.clock)

    def receive_event(self, remote_clock: Dict[str, int]) -> Dict[str, int]:
        for nid, val in remote_clock.items():
            self.clock[nid] = max(self.clock.get(nid, 0), val)
        self.clock[self.node_id] += 1
        return dict(self.clock)

    @staticmethod
    def compare(c1: Dict[str, int], c2: Dict[str, int]) -> Literal["BEFORE", "AFTER", "CONCURRENT", "EQUAL"]:
        c1_leq_c2 = all(c1.get(k, 0) <= c2.get(k, 0) for k in set(c1) | set(c2))
        c2_leq_c1 = all(c2.get(k, 0) <= c1.get(k, 0) for k in set(c1) | set(c2))

        if c1_leq_c2 and c2_leq_c1:
            return "EQUAL"
        if c1_leq_c2 and not c2_leq_c1:
            return "BEFORE"
        if c2_leq_c1 and not c1_leq_c2:
            return "AFTER"
        return "CONCURRENT"


if __name__ == "__main__":
    print("==> Running Exercise 4.1: Vector Clocks & Causality...")
    nodes = ["NodeA", "NodeB", "NodeC"]

    clock_a = VectorClock("NodeA", nodes)
    clock_b = VectorClock("NodeB", nodes)

    # Node A does local work: [1, 0, 0]
    clock_a.tick()

    # Node A sends message to Node B: [2, 0, 0]
    msg_clock = clock_a.send_event()

    # Node B receives message: max([0,0,0], [2,0,0]) + tick => [2, 1, 0]
    clock_b.receive_event(msg_clock)

    # Causality test: event on A happened-before event on B
    relation = VectorClock.compare(msg_clock, clock_b.clock)
    assert relation == "BEFORE", f"Expected BEFORE, got {relation}"

    # Node A and Node B execute independent concurrent events
    clock_a.tick() # A: [3, 0, 0]
    clock_b.tick() # B: [2, 2, 0]

    relation_concurrent = VectorClock.compare(clock_a.clock, clock_b.clock)
    assert relation_concurrent == "CONCURRENT", f"Expected CONCURRENT, got {relation_concurrent}"

    print(f"[PASS] Exercise 4.1 verified (Detected causal BEFORE and CONCURRENT states).")
