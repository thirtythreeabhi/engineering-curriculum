# Engineering Curriculum Standalone Exercises & Guided Labs

Comprehensive set of **23 self-verifying reference exercises** (`volume1/`–`volume5/`) and **6 hands-on debugging & coding katas** (`labs/`) mapped directly to the restructured 5-volume curriculum.

---

## Volume 1: Backend Engineering (`exercises/volume1/`)

| File | Chapter | Topic |
| :--- | :--- | :--- |
| `ex03_python_asyncio_event_loop.py` | Ch 2 & Ch 4 (`ch02-async-concurrency`, `ch04-python-fastapi`) | CPython `asyncio` cooperative multitasking, bounded semaphores, and timeout cancellation |
| `ex01_php_cow_zval.php` | Ch 3 (`ch03-modern-php`) | PHP Zend Engine Copy-on-Write (`CoW`), `&$var` reference semantics, and `gc_collect_cycles()` |
| `ex02_php_pdo_prepared_transactions.php` | Ch 5 (`ch05-databases-sql-orm`) | Real SQLite PDO / `libsqlite3` prepared statements, `BEGIN IMMEDIATE`, `CHECK (balance_cents >= 0)`, and integer cents |
| `ex04_sql_mvcc_isolation.sql` | Ch 5 (`ch05-databases-sql-orm`) | SQLite `BEGIN IMMEDIATE` + solvency constraints, with companion PostgreSQL `REPEATABLE READ` + `FOR UPDATE` reference |
| `ex05_jwt_timing_safe_verifier.py` | Ch 6 (`ch06-auth-security`) | Timing-safe HMAC-SHA256 JWT verification enforcing `alg == "HS256"`, rejecting `alg: none` / `RS256`, and handling malformed input |

---

## Volume 2: AI Engineering (`exercises/volume2/`)

| File | Chapter | Topic |
| :--- | :--- | :--- |
| `ex01_vector_math_cosine.py` | Ch 1 (`ch01-embeddings-vector-db`) | Dense vector dot products, Euclidean L2 norms, cosine similarity, and k-NN search |
| `ex02_bm25_tf_idf_search.py` | Ch 3 (`ch03-retrieval-reranking`) | Okapi BM25 sparse retrieval with TF saturation and document length normalization |
| `ex03_reciprocal_rank_fusion.py` | Ch 3 (`ch03-retrieval-reranking`) | Non-parametric Reciprocal Rank Fusion (`RRF`) combining dense and sparse rankings |
| `ex04_agent_state_reducer.py` | Ch 5 (`ch05-langgraph`) | LangGraph-style typed channel reducers (including absent initial keys and deterministic parallel branch merges) |
| `ex05_rag_triad_evaluator.py` | Ch 6 (`ch06-llm-evaluations`) | Deterministic lexical & negation-aware Groundedness, Answer Relevance, and Context Precision@K |

---

## Volume 3: Cloud & DevSecOps (`exercises/volume3/`)

| File | Chapter | Topic |
| :--- | :--- | :--- |
| `ex01_azure_rbac_least_privilege.py` | Ch 1 & Ch 5 (`ch01-azure-fundamentals`, `ch05-infrastructure-security`) | Azure RBAC evaluation with per-block `notActions` subtraction and multi-block union |
| `ex02_terraform_dag_resolver.py` | Ch 4 (`ch04-terraform-iac`) | Terraform Directed Acyclic Graph (`DAG`) topological sort and parallel execution waves |
| `ex03_semgrep_sast_matcher.py` | Ch 7 (`ch07-devsecops`) | Python `ast.parse` + `ast.NodeVisitor` SAST scanner for SQLi taint, `pickle`, and hardcoded secrets |
| `ex04_spdx_sbom_parser.py` | Ch 7 (`ch07-devsecops`) | SPDX 2.3 SBOM license auditor supporting compound `AND` / `OR` / `WITH` expressions |

---

## Volume 4: Distributed Systems (`exercises/volume4/`)

| File | Chapter | Topic |
| :--- | :--- | :--- |
| `ex01_vector_clocks.py` | Ch 1 (`ch01-distributed-fundamentals`) | Vector Clocks for causal ordering and concurrency conflict detection |
| `ex02_raft_election_sim.py` | Ch 2 (`ch02-cap-consistency`) | Raft leader election with majority quorum, log up-to-date checks, and split-vote recovery |
| `ex03_outbox_pattern_relay.py` | Ch 3 & Ch 8 (`ch03-transactions-concurrency`, `ch08-sagas-cqrs-eventsourcing`) | Transactional Outbox pattern eliminating dual-write failure modes |
| `ex04_distributed_lock_fencing.py` | Ch 7 (`ch07-distributed-locking`) | Distributed locks with active lease TTL checks and monotonic fencing tokens |
| `ex05_circuit_breaker.py` | Ch 9 (`ch09-reliability-fault-tolerance`) | Circuit Breaker (`CLOSED` -> `OPEN` -> `HALF_OPEN`) with consecutive-failure reset on success |

---

## Volume 5: Architecture & Economics (`exercises/volume5/`)

| File | Chapter | Topic |
| :--- | :--- | :--- |
| `ex03_c4_model_validator.py` | Ch 2 (`ch02-c4-architecture`) | C4 architecture model validator enforcing hierarchy and trust boundary rules |
| `ex01_slo_error_budget_burn.py` | Ch 5 (`ch05-slos-slis-slas`) | SRE SLO availability nines, error budgets, and multi-window burn-rate alerts (`14.4x` 1h) |
| `ex04_cloud_finops_optimizer.py` | Ch 8 (`ch08-finops`) | Cloud FinOps cost rightsizer comparing On-Demand vs RIs vs 3-Year Savings Plans |
| `ex02_llm_inference_memory_math.py` | Ch 9 (`ch09-ai-inference-economics`) | LLM inference VRAM sizing in consistent `GiB` (`1024^3`), KV cache math, and `>8` GPU scaling |

---

## Hands-On Guided Labs & Debugging Katas (`exercises/labs/`)

See [`exercises/labs/README.md`](labs/README.md) for instructions. Every lab intentionally fails until you fix the `# BUG:` or complete the `# TODO:`:

| Lab File | Volume & Chapters | Skills Practiced |
| :--- | :--- | :--- |
| `labs/lab_v1_01_async_and_token_bucket_kata.py` | Vol I: Ch 2, Ch 5, Ch 7 | Event-loop blocking bug & token bucket starvation fix |
| `labs/lab_v1_02_jwt_alg_none_kata.py` | Vol I: Ch 6 | Rejecting `alg: none` / `RS256` and malformed JWT inputs |
| `labs/lab_v2_01_recursive_chunker_kata.py` | Vol II: Ch 2 | Recursive separator fallback, window slicing, and chunk overlap |
| `labs/lab_v3_01_ast_sast_visitor_kata.py` | Vol III: Ch 7 | Implementing an `ast.NodeVisitor` SAST scanner |
| `labs/lab_v4_01_lock_fencing_and_breaker_kata.py` | Vol IV: Ch 7, Ch 9 | Lease TTL contention guard & circuit breaker failure reset |
| `labs/lab_v5_01_sli_and_kv_cache_kata.py` | Vol V: Ch 5, Ch 9 | Consistent SLI denominators (`<= 1.0`) & binary `GiB` KV-cache sizing |

---

## Running All Reference Exercises

Execute the automated test runner (runs all 23 self-verifying reference exercises):

```bash
./run-all-exercises.sh
```
