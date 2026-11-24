# Project 04: Asynchronous SQLAlchemy 2.0 with asyncpg Connection Pool & Batched Upserts

High-concurrency data persistence layer leveraging SQLAlchemy 2.0 async engine, asyncpg connection pooling, transactional context managers, and atomic batched upserts (`ON CONFLICT DO UPDATE`).

## Architectural Capabilities

1. **Async Engine & Connection Pooling**:
   - `create_async_engine` with tuned pooling parameters (`pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=1800`).
   - Prevents connection starvation under peak load and recovers dropped TCP connections automatically.

2. **Async Context Managers (`session.begin()`)**:
   - Clean async context manager patterns guarantee ACID boundaries:
     ```python
     async with db.session() as session:
         async with session.begin():
             await repo.batched_upsert(batch)
     ```
   - Automatically issues `COMMIT` upon exit or `ROLLBACK` on any raised exception.

3. **Atomic Batched Upserts (`ON CONFLICT DO UPDATE`)**:
   - Avoids N+1 SELECT-before-INSERT patterns by offloading reconciliation directly to the database engine via `ON CONFLICT (sku) DO UPDATE SET ...`.
   - Supports both PostgreSQL (`asyncpg`) and SQLite (`aiosqlite`) dialects.

4. **Concurrent Processing**:
   - Safely executes concurrent batch streams using Python's `asyncio.gather`.

## Directory Structure

```
p04-async-db-sqlalchemy/
├── README.md
├── requirements.txt
├── src/
│   ├── database.py
│   ├── models.py
│   ├── repository.py
│   └── service.py
└── tests/
    └── test_async_sqlalchemy.py
```

## Running the Pytest Suite

```bash
PYTHONPATH=. pytest tests/ -v
```
