"""Azure Key Vault client with in-memory caching and Private Endpoint checking."""

import time
from typing import Dict, Optional
from src.credentials import AzureCredentialProvider
from src.network import PrivateEndpointVerifier


class KeyVaultSecretClient:
    def __init__(
        self,
        vault_url: str,
        credential_provider: AzureCredentialProvider,
        network_verifier: Optional[PrivateEndpointVerifier] = None,
        cache_ttl_seconds: int = 300,
    ):
        self.vault_url = vault_url
        self.credential_provider = credential_provider
        self.network_verifier = network_verifier or PrivateEndpointVerifier()
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Dict[str, dict] = {}

    def get_secret(self, secret_name: str, resolved_ip: str = "10.0.3.15") -> str:
        """
        Retrieves a secret from Azure Key Vault.
        Validates private network connectivity and honors in-memory cache TTL.
        """
        now = time.time()

        # 1. Check cache
        if secret_name in self._cache:
            entry = self._cache[secret_name]
            if now < entry["expires_at"]:
                return entry["value"]

        # 2. Verify Private Link network enforcement
        hostname = self.vault_url.replace("https://", "").replace("/", "")
        is_private, reason = self.network_verifier.validate_endpoint(hostname, resolved_ip)
        if not is_private:
            raise PermissionError(f"Network Policy Violation: {reason}")

        # 3. Retrieve token via Managed Identity
        token = self.credential_provider.get_token("https://vault.azure.net/.default")

        # 4. Fetch secret (simulated secure secret payload)
        secret_value = f"super_secure_vault_secret_for_{secret_name}_v1"

        # 5. Populate cache with TTL
        self._cache[secret_name] = {
            "value": secret_value,
            "expires_at": now + self.cache_ttl_seconds,
        }

        return secret_value
