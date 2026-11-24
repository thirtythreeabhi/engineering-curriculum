# Modern Engineering Curriculum: Production Technical Textbook

A comprehensive, multi-volume technical textbook and hands-on curriculum spanning **Backend Engineering**, **AI Engineering**, **Cloud & DevSecOps**, **Distributed Systems**, and **Software Architecture & Engineering Economics**.

Designed for comfortable, rigorous self-study over several months, combining the clarity and readability of Manning and O'Reilly engineering books with university-level technical depth.

---

## Curriculum Structure

```
engineering-curriculum/
├── curriculum-map.pdf                # Visual dependency graphs and reading tracks
├── master-textbook.pdf               # Complete unified 5-volume master edition (~300 pages)
├── volume-1-backend.pdf              # Volume I: Backend Engineering
├── volume-2-ai-engineering.pdf       # Volume II: AI Engineering
├── volume-3-cloud-devsecops.pdf      # Volume III: Cloud Engineering & DevSecOps
├── volume-4-distributed-systems.pdf  # Volume IV: Distributed Systems
├── volume-5-architecture-finops.pdf  # Volume V: Architecture & Engineering Economics
├── Makefile                          # Unified build automation
├── latex/                            # Complete LaTeX source documents & TikZ diagrams
├── exercises/                        # Standalone runnable exercises & solutions
└── projects/                         # 12 complete, production-grade reference projects
```

---

## The Five Volumes

### [Volume I: Backend Engineering](volume-1-backend.pdf)
1. **Modern PHP Engineering**: PHP-FPM execution model, Zend Engine, OPcache, JIT compilation, strict types, zvals & memory refcounting, Copy-on-Write (CoW), cyclic garbage collection, closures & scope with `Closure::bind`, PSR middleware, webhooks with HMAC-SHA256 signature verification, replay windows, Redis idempotency.
2. **Python and FastAPI**: CPython bytecode, GIL mechanics, free-threaded Python, asyncio event loop, `epoll`/`kqueue` selectors, coroutine scheduling, Starlette ASGI, Pydantic v2 Rust engine, dependency injection.
3. **Backend Architecture, HTTP and APIs**: HTTP/1.1 vs HTTP/2 multiplexing vs HTTP/3 QUIC, RESTful design, WebSockets, Server-Sent Events, gRPC & Protocol Buffers.
4. **Databases, SQL and ORM Design**: PostgreSQL internals, shared buffers, WAL, B-Trees, `EXPLAIN (ANALYZE, BUFFERS)` execution plans, MVCC, isolation levels, row locking (`SELECT FOR UPDATE`, `SKIP LOCKED`), Active Record vs Data Mapper, N+1 query resolution.
5. **Asynchronous Programming and Concurrency**: Cooperative vs preemptive multitasking, OS threads vs green threads/fibers, CSP channels, actor model, PHP 8.1 Fibers & Revolt.
6. **Authentication, Authorization and Security**: Argon2id vs bcrypt, session fixation defenses, JWT mechanics & signature pitfalls (RS256 vs HS256), OAuth 2.0 PKCE, RBAC/ABAC/ReBAC, OWASP Top 10 mitigations.
7. **Testing and Production Reliability**: Testing pyramid, PHPUnit/pytest, mutation testing with Infection, Testcontainers, circuit breakers, rate limiters (token bucket, leaky bucket).

### [Volume II: AI Engineering](volume-2-ai-engineering.pdf)
1. **LangGraph & State Machines**: Pregel execution model, supersteps, StateGraph topology, typed channel reducers, Postgres checkpointing, human-in-the-loop interrupts, time-travel debugging.
2. **Production-Grade RAG**: Document parsing, semantic vs recursive chunking, chunk fragmentation, lost-in-the-middle mitigations, parent-document retrieval, multi-vector indexing, contextual retrieval.
3. **Embeddings and Vector Databases**: Vector space geometry, cosine/dot-product similarity, curse of dimensionality, Flat vs IVF vs HNSW graph navigation ($M$, $efConstruction$), DiskANN, Qdrant/pgvector internals.
4. **Retrieval Algorithms and Reranking**: BM25 sparse search, hybrid fusion with Reciprocal Rank Fusion (RRF), Cross-Encoder rerankers vs Bi-Encoders, query transformation (HyDE).
5. **Agent Architectures and Orchestration**: Cognitive patterns (ReAct, Plan-and-Solve, Reflexion), function calling schemas, tool execution loops, multi-agent supervisor/worker models.
6. **LLM Evaluations**: Ragas and TruLens, Groundedness/Faithfulness, Answer Relevance, Context Precision, synthetic test datasets, LLM-as-a-judge calibration.
7. **Observability and Tracing**: OpenTelemetry semantic conventions for AI, distributed traces & spans, token and cost attribution, latency percentiles (TTFT, ITL), Langfuse.

### [Volume III: Cloud Engineering & DevSecOps](volume-3-cloud-devsecops.pdf)
1. **Azure Fundamentals and Architecture**: Resource hierarchy, VNets, Subnets, NSGs, Azure Firewall, Private Endpoints & Private Link, App Services & Container Apps.
2. **Azure OpenAI and Azure AI Search**: Enterprise provisioning, PTU vs Pay-As-You-Go, content filters, private endpoint security, Azure AI Search vector indexing, hybrid search, semantic rankers.
3. **Docker and Kubernetes Internals**: Linux namespaces, cgroups v2 quotas, overlay2 filesystem, runc/containerd OCI runtimes. Kubernetes control plane (`kube-apiserver`, `etcd` Raft, scheduler), worker node components (`kubelet`), Pods, Deployments, Services, Ingress, HPA, KEDA.
4. **CI/CD Pipelines**: Workflow triggers, GitHub Actions runner architecture, caching, Blue-Green deployments, Canary rollouts, automated rollbacks.
5. **DevSecOps**: Shift-left security, SAST (Semgrep), SCA (Trivy), secret scanning (TruffleHog), container signing (Cosign), Software Bill of Materials (SBOM via Syft), SLSA provenance.
6. **Terraform and Infrastructure as Code**: Declarative HCL graph construction, Directed Acyclic Graph (DAG) walk, remote state storage, state locking with Azure Blob leases, drift detection and reconciliation, reusable modules.
7. **Infrastructure Security**: Zero Trust architecture, least privilege access, mTLS with SPIFFE/SPIRE, workload identity federation, Azure Key Vault secret management.

### [Volume IV: Distributed Systems](volume-4-distributed-systems.pdf)
1. **Distributed Systems Fundamentals**: Physical limits, network latency, packet loss, clock skew (NTP drift, TrueTime, Lamport/Vector clocks), partial failures, fault models (crash-stop vs Byzantine).
2. **CAP Theorem and Consistency Models**: CAP proof, PACELC theorem, consistency spectrum (Linearizability to Eventual consistency), Raft consensus protocol (leader election, log replication, safety invariants).
3. **Transactions and Concurrency**: Two-Phase Commit (2PC) protocol, prepare/commit phases, coordinator crash failure modes, 3PC, distributed deadlocks.
4. **Messaging Systems**: Message delivery semantics (at-most-once, at-least-once, exactly-once), queues vs streams, dead letter queues (DLQ), poison pill handling.
5. **Kafka and RabbitMQ Internals**: Kafka commit log, partitions, consumer groups, ISR replication, KRaft consensus, zero-copy `sendfile`. RabbitMQ AMQP 0-9-1 exchanges, bindings, Erlang actor model, Raft Quorum queues.
6. **Redis and Caching Topologies**: Redis event loop, internal memory structures (sds, dict, skiplist), LRU/LFU eviction, caching strategies (Cache-Aside, Write-Through, Write-Behind), cache stampedes, Sentinel HA, Cluster hash slots.
7. **Distributed Locking**: Lease mechanics, TTL expiration, the Redlock debate (Kleppmann analysis: GC pauses, clock jumps), fencing tokens, monotonic versioning, database advisory locks.
8. **Sagas, CQRS and Event Sourcing**: The dual-write problem, Transactional Outbox pattern, CDC via Debezium, Orchestration vs Choreography sagas, CQRS read models, event sourcing projections, schema evolution.
9. **Reliability and Fault Tolerance**: Failure detectors (phi-accrual), circuit breakers, bulkheads, load shedding, retry storms, exponential backoff with full jitter, chaos testing.

### [Volume V: Architecture & Engineering Economics](volume-5-architecture-finops.pdf)
1. **C4 Architecture Modeling**: Level 1 (Context), Level 2 (Container), Level 3 (Component), Level 4 (Code); visual modeling rules and audience communication.
2. **UML and Sequence Diagrams**: Lifelines, synchronous/asynchronous calls, activation boxes, combined fragments (`alt`, `opt`, `loop`, `par`), modeling high-concurrency race conditions.
3. **Technical Design Documents (TDD)**: Industry standard RFC structure (Context, Goals/Non-goals, Architecture, API Schema, Storage, Security, Observability, Rollout plan).
4. **Architecture Decision Records (ADRs)**: Michael Nygard format, capturing context, decisions, trade-offs, consequences, and immutable history.
5. **Requirements Engineering**: Functional vs Non-Functional requirements (FURPS+), availability nines, latency percentiles (p50, p95, p99, p99.9), throughput (RPS), durability, RPO & RTO.
6. **Threat Modeling**: STRIDE methodology per element, Data Flow Diagrams (DFDs), trust boundaries, attack trees, security control mapping.
7. **SLOs, SLIs and SLAs**: Mathematical formulas for SLIs, error budget calculations, multi-window multi-burn-rate alerting policies, error budget freeze policies.
8. **Cloud FinOps**: Inform, Optimize, Operate phases; unit economics (cost per user, cost per API request); compute rightsizing, Reserved Instances, Savings Plans, Spot instances.
9. **AI Inference Economics and Cost Optimization**: GPU memory bandwidth bottlenecks, KV cache memory footprint formula ($2 \times n_{\text{layers}} \times d_{\text{model}} \times n_{\text{tokens}} \times \text{bytes}$), TTFT vs throughput, vLLM PagedAttention, speculative decoding, dynamic batching, model quantization (AWQ, FP8), semantic caching.

---

## 12 Production Reference Projects

The curriculum provides 12 practical, production-grade reference implementations in `projects/`:
- `p01-php-db-integration`: Modern PHP 8.3 e-commerce order service with PDO transactions, row locking, and PHPUnit.
- `p02-php-webhook-receiver`: Production webhook receiver with HMAC-SHA256 signature verification, replay tolerance, and Redis idempotency locks.
- `p03-python-fastapi-api`: Production FastAPI microservice with Pydantic v2 schemas, JWT authentication, and structured logging.
- `p04-async-db-sqlalchemy`: Asynchronous SQLAlchemy 2.0 application with asyncpg connection pooling and batch upserts.
- `p05-langgraph-agent-state`: LangGraph research agent with Postgres checkpointer, channel reducers, and human-in-the-loop interrupts.
- `p06-rag-hybrid-rerank`: Hybrid RAG system pairing Qdrant vector search with BM25 sparse retrieval via RRF and Cross-Encoder reranking.
- `p07-llm-eval-pipeline`: Automated LLM evaluation pipeline computing Groundedness, Relevance, and Precision with confidence intervals.
- `p08-azure-secure-app`: Azure-hosted microservice with Managed Identity, Key Vault integration, Private Endpoints, and Application Insights.
- `p09-terraform-infrastructure`: Modular Terraform repo provisioning VNets, subnets, NSGs, private endpoints, and AKS with state locking.
- `p10-cicd-security-pipeline`: Production GitHub Actions pipeline featuring SAST (Semgrep), container scans (Trivy), SBOM generation, and canary deployments.
- `p11-event-driven-microservices`: Distributed order fulfillment system implementing Transactional Outbox, Kafka event streaming, and idempotent consumers.
- `p12-end-to-end-platform`: Multi-service production platform uniting PHP, FastAPI, RabbitMQ, Redis, Postgres, and Prometheus/Grafana observability.

---

## Building the Curriculum

To build all volumes and the master textbook:
```bash
make all
```

To build individual volumes:
```bash
make curriculum-map
make volume-1
make volume-2
make volume-3
make volume-4
make volume-5
make master
```
