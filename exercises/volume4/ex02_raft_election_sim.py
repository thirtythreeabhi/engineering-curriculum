"""
Exercise 4.2: Raft Consensus Leader Election Simulator (with Log Up-to-Date Check)

Problem:
Implement the core leader election mechanism of the Raft consensus algorithm:
1. Nodes start as FOLLOWERS.
2. If election timeout elapses without leader heartbeat, node transitions to CANDIDATE.
3. Candidate increments term, votes for itself, and broadcasts RequestVote RPCs
   including (last_log_index, last_log_term).
4. Voters enforce Raft's election restriction (Section 5.4.1): a candidate receives
   a vote ONLY if its log is at least as up-to-date as the voter's log.
5. If candidate collects votes from a strict majority (quorum = N // 2 + 1), it becomes LEADER;
   otherwise (e.g., split vote or stale log) it steps down to FOLLOWER.
"""

from typing import Dict, List, Literal, Optional, Tuple


class RaftNode:
    def __init__(
        self,
        node_id: str,
        peers: List[str],
        log: Optional[List[Tuple[int, str]]] = None,
    ):
        self.node_id = node_id
        self.peers = peers
        self.current_term = 0
        self.voted_for: Optional[str] = None
        self.state: Literal["FOLLOWER", "CANDIDATE", "LEADER"] = "FOLLOWER"
        # Log entries stored as (term, command)
        self.log: List[Tuple[int, str]] = list(log) if log is not None else []

    @property
    def last_log_index(self) -> int:
        return len(self.log)

    @property
    def last_log_term(self) -> int:
        return self.log[-1][0] if self.log else 0

    def handle_election_timeout(self, cluster: Dict[str, "RaftNode"]) -> bool:
        self.state = "CANDIDATE"
        self.current_term += 1
        self.voted_for = self.node_id
        votes_received = 1  # Vote for self

        for peer_id in self.peers:
            peer = cluster[peer_id]
            vote_granted = peer.request_vote(
                candidate_id=self.node_id,
                candidate_term=self.current_term,
                candidate_last_log_index=self.last_log_index,
                candidate_last_log_term=self.last_log_term,
            )
            if vote_granted:
                votes_received += 1

        quorum = (len(self.peers) + 1) // 2 + 1
        if votes_received >= quorum:
            self.state = "LEADER"
            return True

        self.state = "FOLLOWER"
        return False

    def request_vote(
        self,
        candidate_id: str,
        candidate_term: int,
        candidate_last_log_index: int = 0,
        candidate_last_log_term: int = 0,
    ) -> bool:
        if candidate_term < self.current_term:
            return False

        if candidate_term > self.current_term:
            self.current_term = candidate_term
            self.state = "FOLLOWER"
            self.voted_for = None

        # Raft Section 5.4.1: candidate's log must be at least as up-to-date as voter's
        log_is_up_to_date = (
            candidate_last_log_term > self.last_log_term
            or (
                candidate_last_log_term == self.last_log_term
                and candidate_last_log_index >= self.last_log_index
            )
        )

        if (
            candidate_term == self.current_term
            and (self.voted_for is None or self.voted_for == candidate_id)
            and log_is_up_to_date
        ):
            self.voted_for = candidate_id
            return True

        return False


if __name__ == "__main__":
    print("==> Running Exercise 4.2: Raft Leader Election...")

    # Test 1: Normal 3-node election
    cluster_ids = ["node1", "node2", "node3"]
    cluster = {
        nid: RaftNode(nid, [p for p in cluster_ids if p != nid])
        for nid in cluster_ids
    }
    elected = cluster["node1"].handle_election_timeout(cluster)
    assert elected is True
    assert cluster["node1"].state == "LEADER"
    assert cluster["node1"].current_term == 1
    assert cluster["node2"].voted_for == "node1"
    assert cluster["node3"].voted_for == "node1"

    # Test 2: Stale-candidate rejection via Raft log up-to-date check
    stale_cluster = {
        "node1": RaftNode("node1", ["node2", "node3"], log=[(1, "set x=1")]),
        "node2": RaftNode("node2", ["node1", "node3"], log=[(1, "set x=1"), (2, "set y=2")]),
        "node3": RaftNode("node3", ["node1", "node2"], log=[(1, "set x=1"), (2, "set y=2")]),
    }
    # Stale node1 times out first -> peers update term to 1, but DENY vote due to older log term (1 < 2)
    stale_elected = stale_cluster["node1"].handle_election_timeout(stale_cluster)
    assert stale_elected is False, "Stale candidate with older log MUST NOT win election!"
    assert stale_cluster["node1"].state == "FOLLOWER"
    assert stale_cluster["node2"].voted_for is None

    # Up-to-date node2 times out next -> increments to term 2 and wins quorum
    fresh_elected = stale_cluster["node2"].handle_election_timeout(stale_cluster)
    assert fresh_elected is True
    assert stale_cluster["node2"].state == "LEADER"

    # Test 3: Split-vote in a 4-node cluster (quorum = 3) followed by retry election
    ids_4 = ["n1", "n2", "n3", "n4"]
    split_cluster = {nid: RaftNode(nid, [p for p in ids_4 if p != nid]) for nid in ids_4}
    # Simultaneous Term 1 candidacy: n1 & n2 self-vote, n3 votes n1 (2 votes), n4 votes n2 (2 votes)
    for nid in ids_4:
        split_cluster[nid].current_term = 1
    split_cluster["n1"].state = "CANDIDATE"
    split_cluster["n1"].voted_for = "n1"
    split_cluster["n2"].state = "CANDIDATE"
    split_cluster["n2"].voted_for = "n2"

    n1_votes = 1 + int(split_cluster["n3"].request_vote("n1", 1, 0, 0)) + int(split_cluster["n2"].request_vote("n1", 1, 0, 0))
    n2_votes = 1 + int(split_cluster["n4"].request_vote("n2", 1, 0, 0)) + int(split_cluster["n1"].request_vote("n2", 1, 0, 0))
    assert n1_votes == 2 and n2_votes == 2  # Strict majority of 4 is 3 -> split vote!
    split_cluster["n1"].state = "FOLLOWER"
    split_cluster["n2"].state = "FOLLOWER"

    # Randomized timeout breaks tie in Term 2: n1 times out first and wins 4/4 votes
    assert split_cluster["n1"].handle_election_timeout(split_cluster) is True
    assert split_cluster["n1"].state == "LEADER"
    assert split_cluster["n1"].current_term == 2

    print("[PASS] Exercise 4.2 verified (Quorum election, stale-candidate rejection, and split-vote recovery).")
