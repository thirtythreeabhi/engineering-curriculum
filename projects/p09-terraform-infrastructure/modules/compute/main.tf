resource "azurerm_user_assigned_identity" "aks_identity" {
  name                = "id-aks-controlplane-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
}

resource "azurerm_kubernetes_cluster" "aks" {
  name                      = "aks-enterprise-${var.environment}"
  location                  = var.location
  resource_group_name       = var.resource_group_name
  dns_prefix                = "aks-ent-${var.environment}"
  kubernetes_version        = "1.29"
  private_cluster_enabled   = false
  oidc_issuer_enabled       = true # Required for Azure Workload Identity
  workload_identity_enabled = true # Required for passwordless pod federation

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.aks_identity.id]
  }

  default_node_pool {
    name                = "systempool"
    node_count          = var.aks_node_count
    vm_size             = "Standard_D4s_v5"
    vnet_subnet_id      = var.vnet_subnet_id
    enable_auto_scaling = true
    min_count           = 1
    max_count           = 10
    os_disk_size_gb     = 128
    os_disk_type        = "Ephemeral"

    node_labels = {
      "nodepool" = "system"
      "env"      = var.environment
    }
  }

  network_profile {
    network_plugin     = "azure"
    network_policy     = "azure"
    load_balancer_sku  = "standard"
    service_cidr       = "172.16.0.0/16"
    dns_service_ip     = "172.16.0.10"
  }
}
