output "vnet_id" {
  value = azurerm_virtual_network.vnet.id
}

output "vnet_name" {
  value = azurerm_virtual_network.vnet.name
}

output "aks_subnet_id" {
  value = azurerm_subnet.aks.id
}

output "db_subnet_id" {
  value = azurerm_subnet.db.id
}

output "private_endpoints_subnet_id" {
  value = azurerm_subnet.private_endpoints.id
}
