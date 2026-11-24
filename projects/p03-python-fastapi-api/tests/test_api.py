"""Comprehensive test suite for FastAPI microservice."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_tracing_headers():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "catalog-api"}
    assert "x-request-id" in response.headers
    assert "x-response-time-ms" in response.headers
    # Custom request ID propagation
    custom_id = "test-trace-id-12345"
    res2 = client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert res2.headers["x-request-id"] == custom_id


def test_token_issuance_and_profile():
    # Login as alice
    login_res = client.post(
        "/api/v1/auth/token",
        data={"username": "alice", "password": "alicepassword123"},
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert "read:items" in token_data["scopes"]
    assert "write:items" in token_data["scopes"]

    token = token_data["access_token"]
    # Verify /me endpoint
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "alice"


def test_scope_authorization_enforcement():
    # 1. Login as readonly user
    ro_res = client.post(
        "/api/v1/auth/token",
        data={"username": "readonly_user", "password": "readonly123"},
    )
    ro_token = ro_res.json()["access_token"]

    # Read items should succeed
    get_res = client.get("/api/v1/items", headers={"Authorization": f"Bearer {ro_token}"})
    assert get_res.status_code == 200
    assert len(get_res.json()) >= 1

    # Attempting to write item should be rejected with 403 Forbidden
    post_res = client.post(
        "/api/v1/items",
        json={"title": "Hacker Gadget", "price": 99.99, "stock": 10},
        headers={"Authorization": f"Bearer {ro_token}"},
    )
    assert post_res.status_code == 403
    assert "missing required scope 'write:items'" in post_res.json()["detail"]


def test_pydantic_v2_validation():
    # Login as alice (has write:items)
    token = client.post(
        "/api/v1/auth/token",
        data={"username": "alice", "password": "alicepassword123"},
    ).json()["access_token"]

    # Negative price must trigger validation error 422
    invalid_res = client.post(
        "/api/v1/items",
        json={"title": "Bad Product", "price": -15.00, "stock": 5},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invalid_res.status_code == 422

    # Valid creation
    valid_res = client.post(
        "/api/v1/items",
        json={"title": "Valid Mechanical Keyboard", "price": 129.50, "stock": 20},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert valid_res.status_code == 201
    assert valid_res.json()["title"] == "Valid Mechanical Keyboard"


def test_admin_deletion_scope():
    # Alice attempts deletion -> 403 Forbidden
    alice_token = client.post(
        "/api/v1/auth/token",
        data={"username": "alice", "password": "alicepassword123"},
    ).json()["access_token"]
    del_forbidden = client.delete("/api/v1/items/2", headers={"Authorization": f"Bearer {alice_token}"})
    assert del_forbidden.status_code == 403

    # Admin user attempts deletion -> 204 No Content
    admin_token = client.post(
        "/api/v1/auth/token",
        data={"username": "admin_user", "password": "adminpassword123"},
    ).json()["access_token"]
    del_ok = client.delete("/api/v1/items/2", headers={"Authorization": f"Bearer {admin_token}"})
    assert del_ok.status_code == 204


def test_openapi_schema_generation():
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert schema["info"]["title"] == "Modular Enterprise Catalog API"
    assert "/api/v1/auth/token" in schema["paths"]
    assert "/api/v1/items" in schema["paths"]
