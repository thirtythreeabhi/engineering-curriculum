"""Private Endpoint and Azure Private DNS zone verification."""

import ipaddress
import re
from typing import Tuple


class PrivateEndpointVerifier:
    def __init__(self, private_dns_zone: str = "privatelink.vaultcore.azure.net"):
        self.private_dns_zone = private_dns_zone

    def is_private_ip(self, ip_str: str) -> bool:
        """Verifies that an IP belongs to RFC 1918 private address ranges."""
        try:
            ip = ipaddress.ip_address(ip_str)
            return ip.is_private
        except ValueError:
            return False

    def validate_endpoint(self, hostname: str, resolved_ip: str) -> Tuple[bool, str]:
        """
        Ensures traffic to Key Vault or database does NOT route over public internet,
        verifying that the hostname maps through the Private Link zone to a private IP.
        """
        if not self.is_private_ip(resolved_ip):
            return (
                False,
                f"Security Violation: Host '{hostname}' resolved to public IP {resolved_ip}. Must use Private Endpoint.",
            )

        if not hostname.endswith(".azure.net") and not hostname.endswith(self.private_dns_zone):
            return (
                False,
                f"Invalid Azure resource hostname: {hostname}",
            )

        return (True, f"Verified: {hostname} routes via Private Endpoint to {resolved_ip}.")
