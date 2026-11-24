# Project 06: Two-Stage Hybrid RAG Pipeline (Dense + BM25 + RRF + Cross-Encoder)

Production-grade two-stage retrieval-augmented generation (RAG) search pipeline combining dense vector embeddings (cosine similarity) and sparse keyword retrieval (Okapi BM25) via Reciprocal Rank Fusion (RRF), followed by a high-precision Cross-Encoder reranker.

## Architecture & Mathematical Foundations

1. **Dense Vector Retrieval (Cosine Similarity)**:
   - Captures high-level semantic meaning and conceptual proximity.
   - Computes $\text{sim}(\mathbf{u}, \mathbf{v}) = \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$.

2. **Sparse Retrieval (Okapi BM25)**:
   - Captures exact keyword hits, technical jargon, and code identifiers.
   - Computes probabilistic term-frequency saturation ($k_1=1.5$) with document length normalization ($b=0.75$).

3. **Reciprocal Rank Fusion (RRF)**:
   - Fuses distinct scoring scales into a robust non-parametric ensemble:
     $$\text{RRF}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)} \quad (k=60)$$

4. **Cross-Encoder Reranker**:
   - Performs joint cross-attention scoring across the query and the top candidates retrieved by RRF.
   - Evaluates token coverage and exact terminology alignment to eliminate false positives.

## Directory Structure

```
p06-rag-hybrid-rerank/
├── rag/
│   ├── dense.py
│   ├── fusion.py
│   ├── pipeline.py
│   ├── reranker.py
│   └── sparse.py
├── README.md
├── requirements.txt
└── tests/
    └── test_hybrid_rag.py
```

## Running the Pytest Suite

```bash
PYTHONPATH=. pytest tests/ -v
```
