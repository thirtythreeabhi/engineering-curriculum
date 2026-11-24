"""Azure secure containerized application entrypoint."""

from fastapi import FastAPI, HTTPException
from src.credentials import AzureCredentialProvider
from src.keyvault import KeyVaultSecretClient
from src.network import PrivateEndpointVerifier
from src.telemetry import AppInsightsTelemetry

app = FastAPI(title="Azure Secure App Blueprint", version="1.0.0")

telemetry = AppInsightsTelemetry()
credentials = AzureCredentialProvider()
verifier = PrivateEndpointVerifier()
keyvault = KeyVaultSecretClient(
    vault_url="https://kv-prod-eastus-01.vault.azure.net/",
    credential_provider=credentials,
    network_verifier=verifier,
)


@app.get("/health")
def health():
    return {"status": "healthy", "security": "azure-hardened"}


@app.get("/api/secure-data")
def get_secure_data():
    span = telemetry.start_span("fetch_secure_data_endpoint")
    try:
        # Access Key Vault over private link
        db_password = keyvault.get_secret("db-connection-password", resolved_ip="10.0.3.15")
        telemetry.track_metric("keyvault_secret_accessed", 1.0, {"secret": "db-connection-password"})
        telemetry.end_span(span, 200)
        return {
            "message": "Secure payload retrieved successfully via Private Link",
            "credential_type": credentials.get_token()["token_type"],
            "secret_preview": db_password[:10] + "...",
        }
    except Exception as e:
        telemetry.end_span(span, 500)
        raise HTTPException(status_code=500, detail=str(e))
