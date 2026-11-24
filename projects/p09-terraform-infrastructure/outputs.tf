output "resource_group_name" {
  description = "Provisioned Azure Resource Group name"
  value       = azurerm_resource_group.main.name
}

output "vnet_id" {
  description = "Virtual Network resource ID"
  value       = module.networking.vnet_id
}

output "aks_subnet_id" {
  description = "Subnet allocated for AKS nodes and pods"
  value       = module.networking.aks_subnet_id
}

output "key_vault_id" {
  description = "Azure Key Vault resource ID"
  value       = module.security.key_vault_id
}

output "key_vault_uri" {
  description = "Private Azure Key Vault endpoint URI"
  value       = module.security.key_vault_uri
}

output "aks_cluster_name" {
  description = "Provisioned AKS cluster name"
  value       = module.compute.cluster_name
}

output "aks_oidc_issuer_url" {
  description = "OIDC Issuer URL for Workload Identity federation"
  value       = module.compute.oidc_issuer_url
}
