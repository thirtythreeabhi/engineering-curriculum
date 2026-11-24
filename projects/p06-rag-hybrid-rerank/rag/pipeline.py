"""Two-stage Hybrid RAG Pipeline orchestrator."""

from typing import Dict, List, Tuple
from rag.dense import DenseVectorRetriever
from rag.fusion import ReciprocalRankFusion
from rag.reranker import CrossEncoderReranker
from rag.sparse import OkapiBM25Retriever


class HybridRAGPipeline:
    def __init__(self, dense_dim: int = 64, rrf_k: int = 60):
        self.dense_retriever = DenseVectorRetriever(dim=dense_dim)
        self.sparse_retriever = OkapiBM25Retriever()
        self.fusion = ReciprocalRankFusion(k=rrf_k)
        self.reranker = CrossEncoderReranker()
        self.documents: Dict[str, str] = {}

    def index(self, documents: Dict[str, str]) -> None:
        """Indexes document corpus across both sparse and dense channels."""
        self.documents = dict(documents)
        self.dense_retriever.index(documents)
        self.sparse_retriever.index(documents)

    def search(
        self,
        query: str,
        retrieval_limit: int = 10,
        final_top_k: int = 3,
    ) -> List[Dict[str, any]]:
        """
        Executes two-stage hybrid search:
        Stage 1: Multi-channel retrieval (Dense + Sparse) fused via RRF.
        Stage 2: Cross-Encoder reranking over top candidates.
        """
        dense_results = self.dense_retriever.retrieve(query, top_k=retrieval_limit)
        sparse_results = self.sparse_retriever.retrieve(query, top_k=retrieval_limit)

        fused_candidates = self.fusion.fuse([dense_results, sparse_results], top_k=retrieval_limit)

        reranked = self.reranker.rerank(
            query=query,
            candidates=fused_candidates,
            documents=self.documents,
            top_k=final_top_k,
        )

        return [
            {
                "doc_id": doc_id,
                "score": score,
                "text": self.documents[doc_id],
            }
            for doc_id, score in reranked
        ]
