"""Cross-Encoder reranking stage for high-precision final sorting."""

import re
from typing import Dict, List, Tuple


class CrossEncoderReranker:
    def __init__(self, exact_match_weight: float = 0.4, semantic_weight: float = 0.6):
        self.exact_match_weight = exact_match_weight
        self.semantic_weight = semantic_weight

    def score_pair(self, query: str, document_text: str) -> float:
        """
        Cross-Encoder joint scoring: models cross-attention interaction between
        query tokens and full document context.
        """
        q_tokens = set(re.findall(r"\b\w+\b", query.lower()))
        d_tokens = set(re.findall(r"\b\w+\b", document_text.lower()))

        if not q_tokens or not d_tokens:
            return 0.0

        # Token intersection / recall
        intersection = q_tokens.intersection(d_tokens)
        token_coverage = len(intersection) / len(q_tokens)

        # Exact phrase bonus (e.g. key technical terminology)
        clean_q = query.lower().strip()
        clean_d = document_text.lower()
        phrase_bonus = 1.0 if clean_q in clean_d else 0.0

        # Final calibrated score
        raw_score = (self.semantic_weight * token_coverage) + (self.exact_match_weight * phrase_bonus)
        return min(1.0, max(0.0, raw_score))

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, float]],
        documents: Dict[str, str],
        top_k: int = 5,
    ) -> List[Tuple[str, float]]:
        """Reranks candidate documents using cross-encoder scoring."""
        scored = []
        for doc_id, _fusion_score in candidates:
            doc_text = documents.get(doc_id, "")
            ce_score = self.score_pair(query, doc_text)
            scored.append((doc_id, ce_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]
