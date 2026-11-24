"""Reciprocal Rank Fusion (RRF) algorithm."""

from typing import Dict, List, Tuple


class ReciprocalRankFusion:
    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        ranked_lists: List[List[Tuple[str, float]]],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """
        Merges multiple ranked lists using the RRF scoring function:
        RRF_score(d) = sum(1 / (k + rank(d)))
        """
        rrf_scores: Dict[str, float] = {}

        for ranked_list in ranked_lists:
            for rank_0, (doc_id, _raw_score) in enumerate(ranked_list):
                rank = rank_0 + 1  # 1-based rank
                rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (self.k + rank))

        sorted_candidates = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_candidates[:top_k]
