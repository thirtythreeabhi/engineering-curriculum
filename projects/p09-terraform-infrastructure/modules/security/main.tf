data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "vault" {
  name                          = "kv-ent-${var.environment}-01"
  location                      = var.location
  resource_group_name           = var.resource_group_name
  tenant_id                     = data.azurerm_client_config.current.tenant_id
  sku_name                      = var.key_vault_sku
  soft_delete_retention_days    = 90
  purge_protection_enabled      = true
  public_network_access_enabled = false # Strict private-only access

  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
  }
}

resource "azurerm_private_dns_zone" "vault_dns" {
  name                = "privatelink.vaultcore.azure.net"
  resource_group_name = var.resource_group_name
}

resource "azurerm_private_dns_zone_virtual_network_link" "vnet_link" {
  name                  = "vnet-link-vault-${var.environment}"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.vault_dns.name
  virtual_network_id    = var.vnet_id
}

resource "azurerm_private_endpoint" "vault_pe" {
  name                = "pe-keyvault-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psc-keyvault-${var.environment}"
    private_connection_resource_id = azurerm_key_vault.vault.id
    is_manual_connection           = false
    subresource_names              = ["vault"]
  }

  private_dns_zone_group {
    name                 = "pdz-group-vault"
    private_dns_zone_ids = [azurerm_private_dns_zone.vault_dns.id]
  }
}
