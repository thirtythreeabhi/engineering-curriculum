"""
Exercise 3.1: Azure IAM & RBAC Least-Privilege Evaluation Engine

Problem:
Implement an Azure RBAC policy evaluator:
1. Parses Role Definitions (with one or more Permission blocks containing actions and notActions).
2. Evaluates `notActions` ONLY within the same Permission block (subtracting from that block's
   `actions`), then unions effective permissions across all Permission blocks.
3. Enforces least-privilege principles (default deny unless an effective block permits the action).
"""

import fnmatch
from typing import Dict


class AzureRbacEvaluator:
    def __init__(self, role_definitions: Dict[str, dict]):
        self.roles = role_definitions

    @staticmethod
    def _matches_any(action: str, patterns: list[str]) -> bool:
        action_lower = action.lower()
        return any(fnmatch.fnmatch(action_lower, pat.lower()) for pat in patterns)

    def is_action_allowed(self, role_name: str, requested_action: str) -> bool:
        role = self.roles.get(role_name)
        if not role:
            return False

        permissions = role.get("permissions", [])
        # Effective permissions of a role = union over all Permission blocks of (actions - notActions)
        for perm in permissions:
            actions = perm.get("actions", [])
            not_actions = perm.get("notActions", [])

            if self._matches_any(requested_action, actions) and not self._matches_any(
                requested_action, not_actions
            ):
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
        "StorageReaderWithExplicitReGrant": {
            "permissions": [
                {
                    # Block 1 grants all Storage actions EXCEPT container read/delete
                    "actions": ["Microsoft.Storage/*"],
                    "notActions": [
                        "Microsoft.Storage/storageAccounts/blobServices/containers/read",
                        "Microsoft.Storage/storageAccounts/blobServices/containers/delete",
                    ],
                },
                {
                    # Block 2 explicitly grants container read; Block 1's notActions MUST NOT block Block 2
                    "actions": ["Microsoft.Storage/storageAccounts/blobServices/containers/read"],
                    "notActions": [],
                },
            ],
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

    # 5. Multi-block RBAC: notActions in Block 1 must NOT shadow explicit grant in Block 2
    assert (
        evaluator.is_action_allowed(
            "StorageReaderWithExplicitReGrant",
            "Microsoft.Storage/storageAccounts/blobServices/containers/read",
        )
        is True
    )
    assert (
        evaluator.is_action_allowed(
            "StorageReaderWithExplicitReGrant",
            "Microsoft.Storage/storageAccounts/blobServices/containers/delete",
        )
        is False
    )
    assert (
        evaluator.is_action_allowed(
            "StorageReaderWithExplicitReGrant",
            "Microsoft.Compute/virtualMachines/start/action",
        )
        is False
    )

    print("[PASS] Exercise 3.1 verified (Azure RBAC per-block notActions & multi-block union passed).")
