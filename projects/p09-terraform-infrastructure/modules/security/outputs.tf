output "key_vault_id" {
  value = azurerm_key_vault.vault.id
}

output "key_vault_uri" {
  value = azurerm_key_vault.vault.vault_uri
}

output "private_endpoint_id" {
  value = azurerm_private_endpoint.vault_pe.id
}
