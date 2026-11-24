"""Pytest test suite for Project 12: End-to-End Enterprise Architecture Platform."""

import json
import os
import subprocess
import yaml
import pytest
from fastapi.testclient import TestClient
from services.fastapi_ai_recommendations.main import app as ai_app
from services.async_worker.worker import process_fulfillment_task

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))


def test_docker_compose_topology():
    compose_path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    assert os.path.isfile(compose_path)

    with open(compose_path, "r", encoding="utf-8") as f:
        compose = yaml.safe_load(f)

    services = compose.get("services", {})
    expected_services = [
        "postgres",
        "redis",
        "rabbitmq",
        "php-storefront",
        "ai-recommender",
        "async-worker",
        "prometheus",
        "grafana",
    ]
    for s in expected_services:
        assert s in services, f"docker-compose.yml must define service: {s}"

    # Verify healthchecks configured for infrastructure
    assert "healthcheck" in services["postgres"]
    assert "healthcheck" in services["redis"]
    assert "healthcheck" in services["rabbitmq"]


def test_init_db_sql_script():
    sql_path = os.path.join(PROJECT_ROOT, "init-db/01-init.sql")
    assert os.path.isfile(sql_path)

    with open(sql_path, "r", encoding="utf-8") as f:
        sql = f.read()

    assert "CREATE TABLE IF NOT EXISTS products" in sql
    assert "CREATE TABLE IF NOT EXISTS platform_orders" in sql
    assert "CREATE TABLE IF NOT EXISTS users" in sql
    assert "INSERT INTO products" in sql


def test_prometheus_and_grafana_configs():
    prom_path = os.path.join(PROJECT_ROOT, "observability/prometheus.yml")
    assert os.path.isfile(prom_path)

    with open(prom_path, "r") as f:
        prom = yaml.safe_load(f)
    job_names = [j["job_name"] for j in prom.get("scrape_configs", [])]
    assert "php-storefront" in job_names
    assert "ai-recommender" in job_names

    grafana_path = os.path.join(PROJECT_ROOT, "observability/grafana-dashboard.json")
    assert os.path.isfile(grafana_path)
    with open(grafana_path, "r") as f:
        dash = json.load(f)
    assert dash["uid"] == "platform-e2e-dash"
    assert len(dash["panels"]) >= 2


def test_fastapi_ai_recommendations_endpoint():
    client = TestClient(ai_app)
    res = client.get("/recommendations/42")
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) >= 2
    assert recs[0]["sku"] == "KEYBOARD-MECH"
    assert recs[0]["relevance_score"] >= 0.90

    # Prometheus metrics
    metrics_res = client.get("/metrics")
    assert metrics_res.status_code == 200
    assert "ai_recommendations_served_total" in metrics_res.text


def test_async_worker_fulfillment_task():
    task = {
        "order_id": "ord_e2e_9999",
        "customer_id": "user_101",
        "sku": "LAPTOP-X1",
        "quantity": 1,
    }
    success = process_fulfillment_task(task)
    assert success is True


def test_end_to_end_cross_service_orchestration():
    # 1. AI Recommendation microservice generates cross-sell recommendations
    client = TestClient(ai_app)
    recs = client.get("/recommendations/1").json()
    assert len(recs) > 0
    top_recommended_sku = recs[0]["sku"]

    # 2. Storefront dispatches fulfillment payload to async worker
    fulfillment_payload = {
        "order_id": "ord_integrated_555",
        "user_id": 1,
        "items": [{"sku": top_recommended_sku, "qty": 1}],
    }
    worker_result = process_fulfillment_task(fulfillment_payload)
    assert worker_result is True
