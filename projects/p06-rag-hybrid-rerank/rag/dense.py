"""Dense vector retriever with cosine similarity search."""

import hashlib
import math
from typing import Dict, List, Tuple


def compute_embedding(text: str, dim: int = 64) -> List[float]:
    """
    Generates a deterministic L2-normalized dense embedding vector.
    Uses subword hashing and position weighting to model dense semantic representations.
    """
    vec = [0.0] * dim
    words = text.lower().strip().split()
    if not words:
        return vec

    for i, word in enumerate(words):
        pos_weight = 1.0 / (1.0 + 0.1 * i)
        # Hash character n-grams to distribute across embedding dimensions
        for n in range(2, min(5, len(word) + 1)):
            for j in range(len(word) - n + 1):
                ngram = word[j : j + n]
                h = int(hashlib.md5(ngram.encode("utf-8")).hexdigest(), 16)
                idx = h % dim
                sign = 1.0 if (h >> 8) % 2 == 0 else -1.0
                vec[idx] += sign * pos_weight

    # L2 normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0.0:
        vec = [x / norm for x in vec]
    return vec


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes cosine similarity between two normalized vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    return max(-1.0, min(1.0, dot))


class DenseVectorRetriever:
    def __init__(self, dim: int = 64):
        self.dim = dim
        self.doc_ids: List[str] = []
        self.documents: Dict[str, str] = {}
        self.embeddings: Dict[str, List[float]] = {}

    def index(self, documents: Dict[str, str]) -> None:
        """Indexes documents and computes dense vector representations."""
        self.documents = dict(documents)
        self.doc_ids = list(documents.keys())
        self.embeddings = {
            doc_id: compute_embedding(text, self.dim)
            for doc_id, text in documents.items()
        }

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Returns top_k (doc_id, score) pairs ordered by cosine similarity."""
        query_vec = compute_embedding(query, self.dim)
        scores = [
            (doc_id, cosine_similarity(query_vec, self.embeddings[doc_id]))
            for doc_id in self.doc_ids
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
