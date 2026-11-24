# Production Engineering Reference Projects

This directory contains the 12 complete, production-grade reference engineering projects corresponding to the Modern Engineering Curriculum.

## Master Test Execution

Execute unit tests and integration verifications across all 12 projects with a single command:

```bash
./run-all-tests.sh
```

---

## The 12 Engineering Projects

| Project ID | Directory | Description | Stack / Key Architecture Patterns |
| :--- | :--- | :--- | :--- |
| **p01** | [`p01-php-db-integration`](./p01-php-db-integration/) | Modern PHP 8.3 E-Commerce Order Service | Pure PDO, `SERIALIZABLE` transactions, pessimistic locking (`FOR UPDATE`), prepared statements, typed domain exceptions |
| **p02** | [`p02-php-webhook-receiver`](./p02-php-webhook-receiver/) | Production Webhook Receiver | Constant-time HMAC-SHA256 (`hash_equals`), 5-min timestamp replay defense, atomic Redis idempotency locks, exponential backoff retry worker with DLQ |
| **p03** | [`p03-python-fastapi-api`](./p03-python-fastapi-api/) | Modular FastAPI Microservice | Pydantic v2 schemas, async lifespan handlers, custom request-tracing middleware (`X-Request-ID`), OAuth2 JWT scopes (`read:items`, `write:items`, `admin`), OpenAPI |
| **p04** | [`p04-async-db-sqlalchemy`](./p04-async-db-sqlalchemy/) | Async SQLAlchemy 2.0 Persistence Layer | `create_async_engine`, asyncpg connection pooling, transactional context managers (`session.begin()`), batched atomic upserts (`ON CONFLICT DO UPDATE`) |
| **p05** | [`p05-langgraph-agent-state`](./p05-langgraph-agent-state/) | LangGraph Multi-Tool Research Agent | Typed state schema with channel reducers (`operator.add`), dynamic conditional branching, Human-in-the-Loop (HITL) authorization gate, time-travel checkpoints |
| **p06** | [`p06-rag-hybrid-rerank`](./p06-rag-hybrid-rerank/) | Two-Stage Hybrid RAG Pipeline | Dense vector embeddings (cosine similarity) + Sparse Okapi BM25 retrieval fused via Reciprocal Rank Fusion (RRF), Cross-Encoder reranker |
| **p07** | [`p07-llm-eval-pipeline`](./p07-llm-eval-pipeline/) | Continuous LLM Automated Evaluation Harness | Groundedness/Faithfulness, Answer Relevance, Context Precision@K, synthetic evaluation dataset, LLM-as-a-judge scoring, 95% Bootstrap Confidence Intervals |
| **p08** | [`p08-azure-secure-app`](./p08-azure-secure-app/) | Production Azure Secure App Blueprint | Containerized microservice, Azure Managed Identity / Workload Identity, Azure Key Vault secret access over Private Endpoints, App Insights distributed tracing |
| **p09** | [`p09-terraform-infrastructure`](./p09-terraform-infrastructure/) | Modular Enterprise Terraform Infrastructure | VNet, subnets, zero-trust NSGs (`Deny-All-Inbound`), Private Endpoints, AKS with Azure CNI & Workload Identity, Azure Blob remote state locking, variable validation |
| **p10** | [`p10-cicd-security-pipeline`](./p10-cicd-security-pipeline/) | DevSecOps GitHub Actions CI/CD Pipeline | Linting, unit/integration testing with 80% coverage gate, SAST security analysis (Semgrep), container scanning (Trivy), SBOM generation (Syft SPDX-2.3), canary deployment |
| **p11** | [`p11-event-driven-microservices`](./p11-event-driven-microservices/) | Event-Driven Microservices Fulfillment | Transactional Outbox pattern eliminating dual-write failure modes, Debezium CDC relay streaming to Kafka, idempotent consumers with deduplication table and DLQ |
| **p12** | [`p12-end-to-end-platform`](./p12-end-to-end-platform/) | End-to-End Enterprise Architecture Platform | Multi-service distributed platform: PHP 8.3 storefront, FastAPI AI recommendation microservice, RabbitMQ task broker, Redis cache, Postgres 16 DB, Prometheus/Grafana |
