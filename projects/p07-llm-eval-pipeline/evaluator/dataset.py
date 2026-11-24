"""Synthetic evaluation dataset structures and benchmarks."""

from dataclasses import dataclass
from typing import List


@dataclass
class EvalSample:
    sample_id: str
    query: str
    contexts: List[str]
    response: str
    ground_truth: str
    claims: List[str]


def get_default_evaluation_dataset() -> List[EvalSample]:
    """Returns a curated evaluation dataset for automated test suites."""
    return [
        EvalSample(
            sample_id="eval_001",
            query="What isolation level prevents phantom reads in SQL databases?",
            contexts=[
                "The SQL standard specifies four transaction isolation levels: Read Uncommitted, Read Committed, Repeatable Read, and Serializable.",
                "Serializable isolation prevents all concurrency anomalies including dirty reads, non-repeatable reads, write skew, and phantom reads.",
            ],
            response="The Serializable isolation level prevents phantom reads and all concurrency anomalies in SQL databases.",
            ground_truth="Serializable isolation level prevents phantom reads.",
            claims=[
                "The Serializable isolation level prevents phantom reads.",
                "It eliminates concurrency anomalies in SQL databases.",
            ],
        ),
        EvalSample(
            sample_id="eval_002",
            query="How does Redis provide sub-millisecond latency?",
            contexts=[
                "Redis is an in-memory key-value data store implemented in C.",
                "It processes operations in a single-threaded event loop based on epoll/kqueue, avoiding context switching overhead and disk I/O.",
            ],
            response="Redis achieves sub-millisecond latency by storing data in-memory and running a single-threaded epoll event loop without disk latency.",
            ground_truth="Redis stores data entirely in memory and uses a single-threaded event loop.",
            claims=[
                "Redis stores data in memory.",
                "It uses a single-threaded epoll event loop.",
                "It avoids disk latency during operations.",
            ],
        ),
        EvalSample(
            sample_id="eval_003",
            query="What is the Transactional Outbox pattern?",
            contexts=[
                "The Transactional Outbox pattern writes domain events to an outbox table within the same database transaction as business entities.",
                "A separate CDC process tails the database log to reliably publish events to Apache Kafka without dual-write inconsistencies.",
            ],
            response="The Transactional Outbox pattern records events in an outbox database table atomically within the main transaction, then relays them to Kafka.",
            ground_truth="Transactional Outbox atomically writes events to an outbox table and relays them to message brokers via CDC.",
            claims=[
                "Transactional Outbox records events in an outbox table within the main database transaction.",
                "A CDC process relays the events to Kafka.",
            ],
        ),
    ]
