# Engineering Curriculum Standalone Exercises Catalog

Comprehensive set of 23 standalone, testable, self-verifying engineering exercises spanning the five curriculum volumes:

## Volume 1: Backend Engineering (`exercises/volume1/`)
- `ex01_php_cow_zval.php`: PHP Zend Engine memory allocation, zval reference counting, and Copy-on-Write (CoW) mutation behavior.
- `ex02_php_pdo_prepared_transactions.php`: Atomic transaction rollback, pessimistic row locking, and prepared statements.
- `ex03_python_asyncio_event_loop.py`: CPython asyncio cooperative multitasking, concurrency semaphores, and cancellation.
- `ex04_sql_mvcc_isolation.sql`: PostgreSQL/SQL transactions, MVCC isolation levels, and balance solvency constraints.
- `ex05_jwt_timing_safe_verifier.py`: Timing-safe JWT encoding, HMAC-SHA256 signature verification, and expiration handling.

## Volume 2: AI Engineering (`exercises/volume2/`)
- `ex01_vector_math_cosine.py`: Dense vector dot products, Euclidean L2 norms, cosine similarity, and k-NN search.
- `ex02_bm25_tf_idf_search.py`: Okapi BM25 keyword search with TF saturation and document length normalization.
- `ex03_reciprocal_rank_fusion.py`: Non-parametric Reciprocal Rank Fusion (RRF) combining dense and sparse rankings.
- `ex04_agent_state_reducer.py`: LangGraph-style agent state engine with typed channel reducers (`operator.add`).
- `ex05_rag_triad_evaluator.py`: Groundedness, Answer Relevance, and Context Precision RAG evaluation metrics.

## Volume 3: Cloud & DevSecOps (`exercises/volume3/`)
- `ex01_azure_rbac_least_privilege.py`: Azure IAM/RBAC policy evaluator with explicit notActions denylist overrides.
- `ex02_terraform_dag_resolver.py`: Terraform Directed Acyclic Graph (DAG) topological sort and parallel execution waves.
- `ex03_semgrep_sast_matcher.py`: SAST rule pattern matcher detecting SQLi, pickle deserialization, and hardcoded secrets.
- `ex04_spdx_sbom_parser.py`: SPDX 2.3 Software Bill of Materials (SBOM) license compliance auditor.

## Volume 4: Distributed Systems (`exercises/volume4/`)
- `ex01_vector_clocks.py`: Vector Clocks for causal ordering and concurrency conflict detection.
- `ex02_raft_election_sim.py`: Raft consensus leader election state machine with randomized timeouts and quorum votes.
- `ex03_outbox_pattern_relay.py`: Transactional Outbox pattern eliminating dual-write failure modes.
- `ex04_distributed_lock_fencing.py`: Distributed locks with monotonically increasing fencing tokens (Martin Kleppmann analysis).
- `ex05_circuit_breaker.py`: Circuit Breaker state machine (CLOSED -> OPEN -> HALF-OPEN -> CLOSED) with fallback execution.

## Volume 5: Architecture & Economics (`exercises/volume5/`)
- `ex01_slo_error_budget_burn.py`: SRE SLO availability nines, error budgets, and multi-window burn rate alerts (14.4x 1h).
- `ex02_llm_inference_memory_math.py`: LLM inference economics, KV cache memory formulas, GQA, and GPU capacity planning.
- `ex03_c4_model_validator.py`: C4 architecture model validator enforcing hierarchy and trust boundary rules.
- `ex04_cloud_finops_optimizer.py`: Cloud FinOps cost rightsizer comparing On-Demand vs RIs vs 3-Year Savings Plans.

## Running All Exercises

Execute the automated test runner:

```bash
./run-all-exercises.sh
```
