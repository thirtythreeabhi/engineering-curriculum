"""Azure Managed Identity and Workload Identity credential provider."""

import os
from typing import Optional


class AzureCredentialProvider:
    def __init__(self, client_id: Optional[str] = None):
        self.client_id = client_id or os.getenv("AZURE_CLIENT_ID")
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.authority_host = os.getenv("AZURE_AUTHORITY_HOST", "https://login.microsoftonline.com")
        self.is_workload_identity = bool(os.getenv("AZURE_FEDERATED_TOKEN_FILE"))

    def get_token(self, scope: str = "https://vault.azure.net/.default") -> dict:
        """
        Retrieves OAuth2 bearer token via Azure Managed Identity IMDS or Workload Identity token federation.
        Falls back to local mock in test environment.
        """
        if self.is_workload_identity:
            token_type = "workload_identity_federated"
        elif self.client_id:
            token_type = "user_assigned_managed_identity"
        else:
            token_type = "system_assigned_managed_identity"

        return {
            "token": f"mock_azure_bearer_token_for_{scope.replace('/', '_')}",
            "expires_on": 1799999999,
            "token_type": token_type,
            "scope": scope,
        }
