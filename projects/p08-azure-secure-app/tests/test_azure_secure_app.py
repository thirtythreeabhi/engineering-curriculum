"""Pytest test suite for Azure secure app blueprint."""

import os
import yaml
import pytest
from src.credentials import AzureCredentialProvider
from src.keyvault import KeyVaultSecretClient
from src.network import PrivateEndpointVerifier
from src.telemetry import AppInsightsTelemetry


def test_managed_identity_token_retrieval():
    provider = AzureCredentialProvider(client_id="test-client-guid-001")
    token_info = provider.get_token("https://vault.azure.net/.default")
    assert "token" in token_info
    assert token_info["token_type"] == "user_assigned_managed_identity"
    assert token_info["scope"] == "https://vault.azure.net/.default"


def test_private_endpoint_network_validation():
    verifier = PrivateEndpointVerifier()

    # Private IP in 10.0.0.0/8 range must succeed
    ok_1, _ = verifier.validate_endpoint("kv-prod.vaultcore.azure.net", "10.0.3.15")
    assert ok_1 is True

    # Private IP in 172.16.0.0/12 range must succeed
    ok_2, _ = verifier.validate_endpoint("kv-prod.vaultcore.azure.net", "172.20.1.100")
    assert ok_2 is True

    # Public internet IP (e.g., 20.42.100.5) must be REJECTED
    ok_pub, reason = verifier.validate_endpoint("kv-prod.vaultcore.azure.net", "20.42.100.5")
    assert ok_pub is False
    assert "Must use Private Endpoint" in reason


def test_keyvault_private_link_access_and_caching():
    credentials = AzureCredentialProvider()
    verifier = PrivateEndpointVerifier()
    client = KeyVaultSecretClient(
        vault_url="https://kv-prod-eastus-01.vault.azure.net/",
        credential_provider=credentials,
        network_verifier=verifier,
        cache_ttl_seconds=60,
    )

    # 1. Fetch secret over private endpoint IP
    secret = client.get_secret("app-encryption-key", resolved_ip="10.0.3.50")
    assert secret == "super_secure_vault_secret_for_app-encryption-key_v1"

    # 2. Verify cache hit (returns immediately without network trip)
    cached_secret = client.get_secret("app-encryption-key", resolved_ip="10.0.3.50")
    assert cached_secret == secret


def test_keyvault_rejection_on_public_ip():
    credentials = AzureCredentialProvider()
    verifier = PrivateEndpointVerifier()
    client = KeyVaultSecretClient(
        vault_url="https://kv-prod-eastus-01.vault.azure.net/",
        credential_provider=credentials,
        network_verifier=verifier,
    )

    with pytest.raises(PermissionError, match="Must use Private Endpoint"):
        client.get_secret("app-encryption-key", resolved_ip="52.179.10.20")


def test_appinsights_telemetry_tracking():
    telemetry = AppInsightsTelemetry()
    span = telemetry.start_span("database_read_query")
    ended = telemetry.end_span(span, status_code=200)

    assert ended["name"] == "database_read_query"
    assert "duration_ms" in ended
    assert ended["status_code"] == 200

    telemetry.track_metric("http_requests_total", 42.0)
    assert len(telemetry.recorded_metrics) == 1
    assert telemetry.recorded_metrics[0]["name"] == "http_requests_total"


def test_k8s_manifest_security_hardening():
    manifest_path = os.path.join(os.path.dirname(__file__), "../k8s/deployment.yaml")
    with open(manifest_path, "r") as f:
        doc = yaml.safe_load(f)

    spec = doc["spec"]["template"]["spec"]
    pod_sec = spec["securityContext"]
    assert pod_sec["runAsNonRoot"] is True
    assert pod_sec["runAsUser"] == 10001

    container = spec["containers"][0]
    container_sec = container["securityContext"]
    assert container_sec["readOnlyRootFilesystem"] is True
    assert container_sec["allowPrivilegeEscalation"] is False
    assert "ALL" in container_sec["capabilities"]["drop"]
