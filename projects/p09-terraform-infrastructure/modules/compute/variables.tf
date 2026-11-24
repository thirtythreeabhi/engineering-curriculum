variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
}

variable "environment" {
  type = string
}

variable "aks_node_count" {
  type = number
}

variable "vnet_subnet_id" {
  type = string
}
