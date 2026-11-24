# Project 08: Production Azure Application Blueprint (Managed Identity, Key Vault, Private Endpoint, App Insights)

Enterprise Azure microservice architecture blueprint featuring Managed Identity and Workload Identity authentication, Azure Key Vault secret access over Private Link endpoints, Application Insights distributed tracing, and hardened Kubernetes security contexts.

## Security & Architecture Pillars

1. **Zero Secret Footprint (Managed Identity)**:
   - Uses Azure Managed Identity and AKS Workload Identity token federation (`azure.workload.identity/client-id`).
   - Eliminates hardcoded API keys, database passwords, and long-lived service principal client secrets.

2. **Private Endpoint Network Isolation**:
   - Strictly enforces that communication to Azure Key Vault and SQL databases transits via Azure Private Link (`privatelink.vaultcore.azure.net`) into private RFC 1918 subnets (`10.0.3.0/24`).
   - Blocks egress over the public internet.

3. **Application Insights Observability**:
   - Captures end-to-end distributed transaction traces (`trace_id`, `span_id`), dependency tracking, and custom metrics.

4. **Hardened Container Security**:
   - Multi-stage Docker build executing as unprivileged user (`appuser`, UID 10001).
   - Kubernetes SecurityContext enforces `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, and drops `ALL` Linux capabilities.

## Directory Structure

```
p08-azure-secure-app/
├── Dockerfile
├── k8s/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── serviceaccount.yaml
├── README.md
├── requirements.txt
├── src/
│   ├── credentials.py
│   ├── keyvault.py
│   ├── main.py
│   ├── network.py
│   └── telemetry.py
└── tests/
    └── test_azure_secure_app.py
```

## Running the Tests

```bash
PYTHONPATH=. pytest tests/ -v
```
