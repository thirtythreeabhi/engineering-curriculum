variable "resource_group_name" {
  type        = string
  description = "Parent resource group name"
}

variable "location" {
  type        = string
  description = "Azure region"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "vnet_cidr" {
  type        = string
  description = "Virtual Network CIDR block"
}
