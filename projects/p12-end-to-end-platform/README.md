# Project 12: End-to-End Enterprise Architecture Platform

Full multi-service distributed production platform demonstrating real-world integration between:
1. **Customer Storefront & API Gateway**: High-throughput customer checkout service written in PHP 8.3.
2. **AI Recommendation Microservice**: Asynchronous FastAPI service delivering personalized product recommendations with sub-20ms inference latency.
3. **Distributed Message Broker**: RabbitMQ message exchange managing decoupled order fulfillment workflows.
4. **Asynchronous Background Worker**: Dedicated Python worker executing order fulfillment and inventory reservation.
5. **Relational Data Layer**: PostgreSQL 16 database storing persistent relational schemas and transactional records.
6. **In-Memory Cache**: Redis 7 caching product catalogs and providing distributed idempotency.
7. **Observability Stack**: Prometheus scraping time-series application metrics paired with pre-configured Grafana monitoring dashboards.

## Architecture Topology

```
                       +-------------------------+
                       |   Client Web Browser    |
                       +------------+------------+
                                    |
                                    v
                     +-----------------------------+
                     |    PHP 8.3 Storefront API   |
                     |         (Port 8080)         |
                     +-------+------+--------+-----+
                             |      |        |
         +-------------------+      |        +-------------------+
         | (Cache Queries)          | (REST Recommendations)     | (Publish Task)
         v                          v                            v
  +--------------+       +--------------------+        +--------------------+
  |   Redis 7    |       | FastAPI AI Service |        |     RabbitMQ       |
  |  (Port 6379) |       |    (Port 8000)     |        |  (Ports 5672/15672)|
  +--------------+       +--------------------+        +---------+----------+
         ^                                                       |
         |                                                       v
  +--------------+                                     +--------------------+
  |  Postgres 16 |                                     |   Async Worker     |
  |  (Port 5432) |                                     | (Order Fulfillment)|
  +--------------+                                     +--------------------+
         ^                                                       ^
         |                                                       |
         +-----------------------+-------------------------------+
                                 | (Metrics Scrape)
                                 v
                     +------------------------+
                     |  Prometheus & Grafana  |
                     |    (Ports 9090/3000)   |
                     +------------------------+
```

## Running with Docker Compose

Launch the entire containerized platform with a single command:

```bash
docker compose up -d
```

Check health:
- Storefront API: `http://localhost:8080/health`
- AI Recommendations: `http://localhost:8000/docs`
- RabbitMQ Management: `http://localhost:15672` (rabbit_user / rabbit_password)
- Prometheus Targets: `http://localhost:9090/targets`
- Grafana Dashboard: `http://localhost:3000` (admin / admin)

## Running the Pytest Suite

```bash
PYTHONPATH=. pytest tests/ -v
```
