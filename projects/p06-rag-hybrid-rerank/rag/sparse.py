"""Sparse Okapi BM25 keyword retriever."""

import math
import re
from collections import Counter
from typing import Dict, List, Tuple


def tokenize(text: str) -> List[str]:
    """Tokenize and normalize text into clean words."""
    return re.findall(r"\b\w+\b", text.lower())


class OkapiBM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, str] = {}
        self.doc_ids: List[str] = []
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = Counter()
        self.term_freqs: Dict[str, Counter] = {}

    def index(self, documents: Dict[str, str]) -> None:
        """Builds an inverted index and computes document length statistics."""
        self.documents = dict(documents)
        self.doc_ids = list(documents.keys())
        total_len = 0

        self.doc_freqs.clear()
        self.term_freqs.clear()

        for doc_id, text in documents.items():
            tokens = tokenize(text)
            self.term_freqs[doc_id] = Counter(tokens)
            doc_len = len(tokens)
            self.doc_lengths[doc_id] = doc_len
            total_len += doc_len

            # Update document frequency for distinct terms
            for term in set(tokens):
                self.doc_freqs[term] += 1

        self.avg_doc_len = total_len / max(1, len(self.doc_ids))

    def _idf(self, term: str) -> float:
        n_q = self.doc_freqs.get(term, 0)
        n = len(self.doc_ids)
        # Probabilistic IDF with smoothing
        return math.log(1.0 + (n - n_q + 0.5) / (n_q + 0.5))

    def retrieve(self, query: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """Returns top_k (doc_id, score) pairs ordered by Okapi BM25 score."""
        query_terms = tokenize(query)
        scores: Dict[str, float] = {doc_id: 0.0 for doc_id in self.doc_ids}

        for term in query_terms:
            idf = self._idf(term)
            for doc_id in self.doc_ids:
                tf = self.term_freqs[doc_id].get(term, 0)
                if tf == 0:
                    continue
                doc_len = self.doc_lengths[doc_id]
                norm_len = (1.0 - self.b) + self.b * (doc_len / self.avg_doc_len)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * norm_len
                scores[doc_id] += idf * (numerator / denominator)

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_scores[:top_k]
