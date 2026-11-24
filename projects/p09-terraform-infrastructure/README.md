# Project 09: Modular Enterprise Terraform Infrastructure (VNet, Private Link, AKS, State Locking)

Production-ready Infrastructure as Code (IaC) repository provisioning an enterprise cloud footprint in Microsoft Azure using modular Terraform with remote state locking, least-privilege network security groups, Private Endpoints, and Azure Kubernetes Service (AKS) with Workload Identity.

## Architecture Highlights

1. **Modular Decomposition**:
   - `modules/networking`: VNet address space partitioning (`10.0.0.0/16`), dedicated subnets for AKS, databases, and Private Endpoints. Zero-trust NSG with default `Deny-All-Inbound`.
   - `modules/security`: Azure Key Vault with `public_network_access_enabled = false`, Private Endpoint, and `privatelink.vaultcore.azure.net` Private DNS Zone.
   - `modules/compute`: Azure Kubernetes Service (AKS) provisioned with Azure CNI, Ephemeral OS disks, OIDC issuer, and Azure Workload Identity.

2. **Distributed Remote State Locking**:
   - Configures the `azurerm` backend with Azure Blob native lease locking and Azure AD OAuth authentication (`use_azuread_auth = true`) to eliminate concurrent apply corruption.

3. **Input Variable Validation**:
   - Enforces environment constraints (`dev`, `staging`, `prod`), CIDR subnet validation (`can(cidrnetmask(...))`), and node pool capacity limits (`1 <= count <= 50`).

## Directory Structure

```
p09-terraform-infrastructure/
├── main.tf
├── modules/
│   ├── compute/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   ├── networking/
│   │   ├── main.tf
│   │   ├── outputs.tf
│   │   └── variables.tf
│   └── security/
│       ├── main.tf
│       ├── outputs.tf
│       └── variables.tf
├── outputs.tf
├── providers.tf
├── README.md
├── terraform.tfvars.example
├── tests/
│   └── test_terraform_syntax.py
└── variables.tf
```

## Running the Automated Validation Tests

```bash
pytest tests/ -v
```
