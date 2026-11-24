"""
Exercise 3.1: Azure IAM & RBAC Least-Privilege Evaluation Engine

Problem:
Implement an Azure RBAC policy evaluator:
1. Parses Role Definitions (RoleAssignment, RoleDefinition with actions and notActions).
2. Evaluates whether a principal possesses permission to execute a specific action.
3. Enforces least-privilege principles (explicit Deny / NotAction overrides Allow).
"""

import fnmatch
from typing import Dict, List


class AzureRbacEvaluator:
    def __init__(self, role_definitions: Dict[str, dict]):
        self.roles = role_definitions

    def is_action_allowed(self, role_name: str, requested_action: str) -> bool:
        role = self.roles.get(role_name)
        if not role:
            return False

        permissions = role.get("permissions", [])
        for perm in permissions:
            actions = perm.get("actions", [])
            not_actions = perm.get("notActions", [])

            # Check if explicitly blocked by notActions
            for not_act in not_actions:
                if fnmatch.fnmatch(requested_action.lower(), not_act.lower()):
                    return False

            # Check if granted by actions
            for act in actions:
                if fnmatch.fnmatch(requested_action.lower(), act.lower()):
                    return True

        return False


if __name__ == "__main__":
    print("==> Running Exercise 3.1: Azure RBAC Least-Privilege Evaluation...")
    roles = {
        "KeyVaultSecretsUser": {
            "permissions": [{
                "actions": [
                    "Microsoft.KeyVault/vaults/secrets/getSecret/action",
                    "Microsoft.KeyVault/vaults/secrets/readMetadata/action",
                ],
                "notActions": [
                    "Microsoft.KeyVault/vaults/secrets/deleteSecret/action",
                ],
            }],
        },
        "Contributor": {
            "permissions": [{
                "actions": ["*"],
                "notActions": ["Microsoft.Authorization/*/Delete", "Microsoft.Authorization/*/Write"],
            }],
        },
    }

    evaluator = AzureRbacEvaluator(roles)

    # 1. Read secret should be allowed
    assert evaluator.is_action_allowed("KeyVaultSecretsUser", "Microsoft.KeyVault/vaults/secrets/getSecret/action") is True

    # 2. Delete secret should be disallowed
    assert evaluator.is_action_allowed("KeyVaultSecretsUser", "Microsoft.KeyVault/vaults/secrets/deleteSecret/action") is False

    # 3. Contributor should allow VM restart
    assert evaluator.is_action_allowed("Contributor", "Microsoft.Compute/virtualMachines/restart/action") is True

    # 4. Contributor should disallow role deletion
    assert evaluator.is_action_allowed("Contributor", "Microsoft.Authorization/roleAssignments/Delete") is False

    print("[PASS] Exercise 3.1 verified (Azure RBAC least-privilege logic passed).")
