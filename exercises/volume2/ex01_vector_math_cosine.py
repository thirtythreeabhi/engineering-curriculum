"""
Exercise 2.1: Vector Mathematics and Cosine Similarity

Problem:
Implement high-performance dense vector math from scratch:
1. Vector dot product and Euclidean L2 norm.
2. Cosine similarity between arbitrary N-dimensional vectors.
3. K-Nearest Neighbors (k-NN) search across a dense vector index.
"""

import math
from typing import List, Tuple


def dot_product(v1: List[float], v2: List[float]) -> float:
    return sum(a * b for a, b in zip(v1, v2))


def l2_norm(v: List[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    norm1 = l2_norm(v1)
    norm2 = l2_norm(v2)
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot_product(v1, v2) / (norm1 * norm2)


def knn_search(
    query_vector: List[float],
    index: List[Tuple[str, List[float]]],
    k: int = 2,
) -> List[Tuple[str, float]]:
    scored = [
        (doc_id, cosine_similarity(query_vector, vec))
        for doc_id, vec in index
    ]
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


if __name__ == "__main__":
    print("==> Running Exercise 2.1: Vector Math & Cosine Similarity...")
    # Orthogonal vectors should have similarity 0.0
    assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-6
    # Parallel vectors should have similarity 1.0
    assert abs(cosine_similarity([2.0, 3.0], [4.0, 6.0]) - 1.0) < 1e-6

    # k-NN search
    index = [
        ("doc_ai", [0.9, 0.8, 0.1]),
        ("doc_cooking", [0.1, 0.2, 0.9]),
        ("doc_machine_learning", [0.85, 0.75, 0.2]),
    ]
    query = [0.95, 0.85, 0.1]
    top_docs = knn_search(query, index, k=2)

    assert len(top_docs) == 2
    assert top_docs[0][0] in ["doc_ai", "doc_machine_learning"]
    assert top_docs[0][1] > 0.95
    print(f"[PASS] Exercise 2.1 verified (Top match: {top_docs[0][0]} with sim={top_docs[0][1]:.4f}).")
