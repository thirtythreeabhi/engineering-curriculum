"""Pytest suite validating Terraform module structure, variables, and security rules."""

import os
import re
import ipaddress
import pytest

TF_ROOT = os.path.dirname(os.path.dirname(__file__))


def read_tf_file(relative_path: str) -> str:
    path = os.path.join(TF_ROOT, relative_path)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def test_required_files_exist():
    expected_files = [
        "providers.tf",
        "variables.tf",
        "main.tf",
        "outputs.tf",
        "terraform.tfvars.example",
        "modules/networking/main.tf",
        "modules/networking/variables.tf",
        "modules/networking/outputs.tf",
        "modules/security/main.tf",
        "modules/security/variables.tf",
        "modules/security/outputs.tf",
        "modules/compute/main.tf",
        "modules/compute/variables.tf",
        "modules/compute/outputs.tf",
    ]
    for rel_path in expected_files:
        full_path = os.path.join(TF_ROOT, rel_path)
        assert os.path.isfile(full_path), f"Missing expected Terraform file: {rel_path}"


def test_remote_state_backend_locking():
    content = read_tf_file("providers.tf")
    assert 'backend "azurerm"' in content
    assert "use_azuread_auth" in content
    assert "key                  =" in content


def test_variable_validation_rules():
    content = read_tf_file("variables.tf")

    # Environment validation
    assert 'contains(["dev", "staging", "prod"], var.environment)' in content

    # CIDR validation
    assert "can(cidrnetmask(var.vnet_cidr))" in content

    # Node count validation
    assert "var.aks_node_count >= 1 && var.aks_node_count <= 50" in content

    # Key vault SKU validation
    assert 'contains(["standard", "premium"], var.key_vault_sku)' in content


def test_networking_security_rules():
    content = read_tf_file("modules/networking/main.tf")
    assert 'name                       = "Deny-All-Inbound"' in content
    assert 'access                     = "Deny"' in content
    assert 'priority                   = 4096' in content
    assert "azurerm_subnet_network_security_group_association" in content


def test_key_vault_private_endpoint_enforcement():
    content = read_tf_file("modules/security/main.tf")
    assert "public_network_access_enabled = false" in content
    assert "azurerm_private_endpoint" in content
    assert "privatelink.vaultcore.azure.net" in content
    assert "azurerm_private_dns_zone_virtual_network_link" in content


def test_aks_workload_identity_and_cni():
    content = read_tf_file("modules/compute/main.tf")
    assert "oidc_issuer_enabled       = true" in content
    assert "workload_identity_enabled = true" in content
    assert 'network_plugin     = "azure"' in content
