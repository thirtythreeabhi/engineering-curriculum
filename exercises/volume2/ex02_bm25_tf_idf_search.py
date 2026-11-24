"""
Exercise 2.2: Okapi BM25 Keyword Search Engine from Scratch

Problem:
Implement the Okapi BM25 ranking function:
1. Tokenizes and computes Term Frequencies (TF) and Document Frequencies (DF).
2. Computes Robertson-Spärck Jones probabilistic IDF.
3. Applies document length normalization (k1=1.5, b=0.75).
"""

import math
import re
from collections import Counter
from typing import Dict, List, Tuple


class BM25SearchEngine:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: Dict[str, str] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.term_freqs: Dict[str, Counter] = {}
        self.doc_freqs: Counter = Counter()
        self.avg_len: float = 0.0

    def fit(self, corpus: Dict[str, str]) -> None:
        self.docs = corpus
        total_len = 0
        for doc_id, text in corpus.items():
            tokens = re.findall(r"\b\w+\b", text.lower())
            self.term_freqs[doc_id] = Counter(tokens)
            length = len(tokens)
            self.doc_lengths[doc_id] = length
            total_len += length
            for t in set(tokens):
                self.doc_freqs[t] += 1
        self.avg_len = total_len / max(1, len(corpus))

    def _idf(self, term: str) -> float:
        n = len(self.docs)
        df = self.doc_freqs.get(term, 0)
        return math.log(1.0 + (n - df + 0.5) / (df + 0.5))

    def search(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        q_tokens = re.findall(r"\b\w+\b", query.lower())
        scores = {doc_id: 0.0 for doc_id in self.docs}

        for term in q_tokens:
            idf = self._idf(term)
            for doc_id in self.docs:
                tf = self.term_freqs[doc_id].get(term, 0)
                if tf == 0:
                    continue
                d_len = self.doc_lengths[doc_id]
                norm_len = (1.0 - self.b) + self.b * (d_len / self.avg_len)
                tf_component = (tf * (self.k1 + 1.0)) / (tf + self.k1 * norm_len)
                scores[doc_id] += idf * tf_component

        return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]


if __name__ == "__main__":
    print("==> Running Exercise 2.2: Okapi BM25 Keyword Search...")
    corpus = {
        "doc1": "Python asyncio provides asynchronous event loops and coroutines for high concurrency.",
        "doc2": "PostgreSQL relational databases support ACID transactions and MVCC row isolation.",
        "doc3": "LangGraph state machine models multi-agent workflows with channel reducers.",
    }
    engine = BM25SearchEngine()
    engine.fit(corpus)
    res = engine.search("asyncio concurrency coroutines", top_k=1)
    assert res[0][0] == "doc1"
    assert res[0][1] > 0.0
    print(f"[PASS] Exercise 2.2 verified (Matched: {res[0][0]} score={res[0][1]:.4f}).")
