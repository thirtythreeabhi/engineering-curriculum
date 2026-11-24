"""In-memory distributed message broker simulating Apache Kafka."""

from collections import defaultdict
from typing import Any, Dict, List, Optional


class KafkaBroker:
    def __init__(self):
        # topic -> list of messages
        self.topics: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        # (consumer_group, topic) -> current offset
        self.offsets: Dict[tuple, int] = defaultdict(int)

    def publish(self, topic: str, message: Dict[str, Any]) -> int:
        """Publishes a message to a topic and returns its assigned offset."""
        self.topics[topic].append(message)
        return len(self.topics[topic]) - 1

    def consume(self, topic: str, consumer_group: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        """Consumes unread messages for a given consumer group."""
        current_offset = self.offsets[(consumer_group, topic)]
        messages = self.topics[topic][current_offset : current_offset + max_messages]
        self.offsets[(consumer_group, topic)] = current_offset + len(messages)
        return messages

    def get_all_messages(self, topic: str) -> List[Dict[str, Any]]:
        return list(self.topics[topic])
