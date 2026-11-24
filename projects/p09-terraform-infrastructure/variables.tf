variable "environment" {
  type        = string
  description = "Target deployment environment"
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Variable environment must be one of: 'dev', 'staging', or 'prod'."
  }
}

variable "location" {
  type        = string
  description = "Azure region for resource deployment"
  default     = "eastus2"
}

variable "vnet_cidr" {
  type        = string
  description = "Primary Virtual Network IPv4 address space"
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vnet_cidr))
    error_message = "Variable vnet_cidr must be a valid IPv4 CIDR block (e.g., 10.0.0.0/16)."
  }
}

variable "aks_node_count" {
  type        = number
  description = "Initial number of system nodes in AKS node pool"
  default     = 3

  validation {
    condition     = var.aks_node_count >= 1 && var.aks_node_count <= 50
    error_message = "Variable aks_node_count must be between 1 and 50."
  }
}

variable "key_vault_sku" {
  type        = string
  description = "SKU family for Azure Key Vault"
  default     = "standard"

  validation {
    condition     = contains(["standard", "premium"], var.key_vault_sku)
    error_message = "Variable key_vault_sku must be either 'standard' or 'premium'."
  }
}
