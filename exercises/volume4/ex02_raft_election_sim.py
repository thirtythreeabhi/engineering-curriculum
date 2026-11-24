"""
Exercise 4.2: Raft Consensus Leader Election Simulator

Problem:
Implement the core leader election mechanism of the Raft consensus algorithm:
1. Nodes start as FOLLOWERS.
2. If election timeout elapses without leader heartbeat, node transitions to CANDIDATE.
3. Candidate increments term, votes for itself, and broadcasts RequestVote RPCs.
4. If candidate collects votes from a strict majority (quorum = N // 2 + 1), it becomes LEADER.
5. If split vote occurs, candidate increments term and restarts election.
"""

from typing import Dict, List, Literal


class RaftNode:
    def __init__(self, node_id: str, peers: List[str]):
        self.node_id = node_id
        self.peers = peers
        self.current_term = 0
        self.voted_for: str | None = None
        self.state: Literal["FOLLOWER", "CANDIDATE", "LEADER"] = "FOLLOWER"

    def handle_election_timeout(self, cluster: Dict[str, "RaftNode"]) -> bool:
        # Transition to candidate
        self.state = "CANDIDATE"
        self.current_term += 1
        self.voted_for = self.node_id
        votes_received = 1  # Vote for self

        # Request votes from peers
        for peer_id in self.peers:
            peer = cluster[peer_id]
            vote_granted = peer.request_vote(
                candidate_id=self.node_id,
                candidate_term=self.current_term,
            )
            if vote_granted:
                votes_received += 1

        quorum = (len(self.peers) + 1) // 2 + 1
        if votes_received >= quorum:
            self.state = "LEADER"
            return True

        self.state = "FOLLOWER"
        return False

    def request_vote(self, candidate_id: str, candidate_term: int) -> bool:
        if candidate_term > self.current_term:
            self.current_term = candidate_term
            self.state = "FOLLOWER"
            self.voted_for = None

        if candidate_term == self.current_term and (self.voted_for is None or self.voted_for == candidate_id):
            self.voted_for = candidate_id
            return True

        return False


if __name__ == "__main__":
    print("==> Running Exercise 4.2: Raft Leader Election...")
    cluster_ids = ["node1", "node2", "node3"]
    cluster = {
        nid: RaftNode(nid, [p for p in cluster_ids if p != nid])
        for nid in cluster_ids
    }

    # Node 1 experiences election timeout first
    elected = cluster["node1"].handle_election_timeout(cluster)

    assert elected is True
    assert cluster["node1"].state == "LEADER"
    assert cluster["node1"].current_term == 1
    assert cluster["node2"].state == "FOLLOWER"
    assert cluster["node2"].voted_for == "node1"
    assert cluster["node3"].voted_for == "node1"

    print(f"[PASS] Exercise 4.2 verified (Node 1 elected Leader for Term 1 with quorum).")
