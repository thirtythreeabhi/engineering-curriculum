"""
Exercise 2.3: Reciprocal Rank Fusion (RRF) Algorithm

Problem:
Combine disparate search ranking results (e.g. dense vector ranking and sparse BM25 ranking)
without needing calibrated score normalization.
Formula:
RRF(d) = sum( 1.0 / (k + rank(d)) ) for each list where d appears, with default k=60.
"""

from typing import Dict, List, Tuple


def reciprocal_rank_fusion(
    ranked_runs: List[List[str]],
    k: int = 60,
    top_n: int = 5,
) -> List[Tuple[str, float]]:
    scores: Dict[str, float] = {}

    for run in ranked_runs:
        for zero_rank, doc_id in enumerate(run):
            rank = zero_rank + 1
            scores[doc_id] = scores.get(doc_id, 0.0) + (1.0 / (k + rank))

    sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_docs[:top_n]


if __name__ == "__main__":
    print("==> Running Exercise 2.3: Reciprocal Rank Fusion (RRF)...")
    dense_run = ["doc_A", "doc_B", "doc_C", "doc_D"]
    sparse_run = ["doc_B", "doc_E", "doc_A", "doc_F"]

    fused = reciprocal_rank_fusion([dense_run, sparse_run], k=60, top_n=3)

    # doc_B is rank 2 in dense, rank 1 in sparse -> 1/62 + 1/61 = 0.03252
    # doc_A is rank 1 in dense, rank 3 in sparse -> 1/61 + 1/63 = 0.03226
    assert len(fused) == 3
    assert fused[0][0] == "doc_B"
    assert fused[1][0] == "doc_A"
    print(f"[PASS] Exercise 2.3 verified (Top fused doc: {fused[0][0]} with RRF={fused[0][1]:.5f}).")
