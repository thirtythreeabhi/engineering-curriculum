resource "azurerm_resource_group" "main" {
  name     = "rg-enterprise-network-${var.environment}"
  location = var.location

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Curriculum  = "ModernEngineering"
  }
}

module "networking" {
  source              = "./modules/networking"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  vnet_cidr           = var.vnet_cidr
}

module "security" {
  source              = "./modules/security"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  key_vault_sku       = var.key_vault_sku
  subnet_id           = module.networking.private_endpoints_subnet_id
  vnet_id             = module.networking.vnet_id
}

module "compute" {
  source              = "./modules/compute"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  environment         = var.environment
  aks_node_count      = var.aks_node_count
  vnet_subnet_id      = module.networking.aks_subnet_id
}
