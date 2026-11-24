"""Pytest test suite for Hybrid RAG Pipeline with RRF and Cross-Encoder."""

import pytest
from rag.dense import DenseVectorRetriever
from rag.fusion import ReciprocalRankFusion
from rag.pipeline import HybridRAGPipeline
from rag.reranker import CrossEncoderReranker
from rag.sparse import OkapiBM25Retriever

DOCUMENTS = {
    "doc_sql_mvcc": "PostgreSQL uses Multi-Version Concurrency Control (MVCC) to ensure isolation levels without read locks.",
    "doc_redis_cache": "Redis is an in-memory key-value data store used for sub-millisecond caching and distributed locks.",
    "doc_kafka_outbox": "The Transactional Outbox pattern guarantees at-least-once message delivery to Apache Kafka from relational databases.",
    "doc_k8s_cni": "Kubernetes Container Network Interface (CNI) plugins provide IP address management and pod-to-pod networking.",
    "doc_fastapi_async": "FastAPI leverages Python asyncio and ASGI servers like Uvicorn for asynchronous non-blocking request handling.",
}


def test_dense_retrieval():
    retriever = DenseVectorRetriever()
    retriever.index(DOCUMENTS)
    results = retriever.retrieve("PostgreSQL MVCC transactions", top_k=2)
    assert len(results) == 2
    assert results[0][0] == "doc_sql_mvcc"


def test_bm25_sparse_retrieval():
    retriever = OkapiBM25Retriever()
    retriever.index(DOCUMENTS)
    results = retriever.retrieve("Transactional Outbox Kafka", top_k=2)
    assert len(results) == 2
    assert results[0][0] == "doc_kafka_outbox"


def test_reciprocal_rank_fusion():
    fusion = ReciprocalRankFusion(k=60)
    list1 = [("doc_a", 0.95), ("doc_b", 0.80), ("doc_c", 0.70)]
    list2 = [("doc_b", 12.5), ("doc_a", 10.1), ("doc_d", 5.0)]

    fused = fusion.fuse([list1, list2], top_k=3)
    # doc_a rank in list1=1, list2=2 => 1/61 + 1/62 = 0.01639 + 0.01613 = 0.03252
    # doc_b rank in list1=2, list2=1 => 1/62 + 1/61 = 0.03252
    assert len(fused) == 3
    top_ids = {fused[0][0], fused[1][0]}
    assert top_ids == {"doc_a", "doc_b"}


def test_cross_encoder_reranking():
    reranker = CrossEncoderReranker()
    query = "asynchronous request handling with FastAPI"
    candidates = [("doc_redis_cache", 0.02), ("doc_fastapi_async", 0.015)]
    reranked = reranker.rerank(query, candidates, DOCUMENTS, top_k=2)
    # doc_fastapi_async should be reranked to top because of high token coverage
    assert reranked[0][0] == "doc_fastapi_async"
    assert reranked[0][1] > reranked[1][1]


def test_end_to_end_hybrid_pipeline():
    pipeline = HybridRAGPipeline()
    pipeline.index(DOCUMENTS)

    results = pipeline.search("How does PostgreSQL handle concurrency and isolation?", final_top_k=2)
    assert len(results) == 2
    assert results[0]["doc_id"] == "doc_sql_mvcc"
    assert "MVCC" in results[0]["text"]
