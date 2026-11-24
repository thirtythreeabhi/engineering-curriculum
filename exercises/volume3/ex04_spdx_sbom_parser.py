"""
Exercise 3.4: SPDX 2.3 Software Bill of Materials (SBOM) Analyzer

Problem:
Implement an automated SBOM license auditor that:
1. Parses standard SPDX-2.3 JSON documents.
2. Catalogs package inventory and declared licenses.
3. Enforces an open-source license compliance policy (allowing MIT, Apache-2.0, BSD; flagging GPL copyleft).
"""

import json
from typing import Dict, List, Set


class SbomLicenseAuditor:
    def __init__(self, allowed_licenses: Set[str]):
        self.allowed_licenses = allowed_licenses

    def audit_spdx(self, spdx_json_str: str) -> Dict[str, any]:
        data = json.loads(spdx_json_str)
        packages = data.get("packages", [])

        compliant_packages = []
        violations = []

        for pkg in packages:
            name = pkg.get("name", "unknown")
            version = pkg.get("versionInfo", "unknown")
            license_str = pkg.get("licenseConcluded", "NOASSERTION")

            if license_str in self.allowed_licenses:
                compliant_packages.append({"name": name, "version": version, "license": license_str})
            else:
                violations.append({
                    "name": name,
                    "version": version,
                    "license": license_str,
                    "reason": f"License '{license_str}' is not in approved license whitelist.",
                })

        return {
            "spdx_version": data.get("spdxVersion"),
            "total_packages": len(packages),
            "compliant_count": len(compliant_packages),
            "violation_count": len(violations),
            "violations": violations,
            "status": "APPROVED" if len(violations) == 0 else "NON_COMPLIANT",
        }


if __name__ == "__main__":
    print("==> Running Exercise 3.4: SBOM License Auditor...")
    allowed = {"MIT", "Apache-2.0", "BSD-3-Clause", "ISC"}
    auditor = SbomLicenseAuditor(allowed)

    sample_sbom = """
    {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "enterprise-backend-service",
        "packages": [
            {"name": "fastapi", "versionInfo": "0.110.0", "licenseConcluded": "MIT"},
            {"name": "pydantic", "versionInfo": "2.6.0", "licenseConcluded": "MIT"},
            {"name": "gpl-library", "versionInfo": "1.0.0", "licenseConcluded": "GPL-3.0-only"}
        ]
    }
    """

    report = auditor.audit_spdx(sample_sbom)
    assert report["total_packages"] == 3
    assert report["compliant_count"] == 2
    assert report["violation_count"] == 1
    assert report["violations"][0]["name"] == "gpl-library"
    assert report["status"] == "NON_COMPLIANT"

    print(f"[PASS] Exercise 3.4 verified (Identified license violation: {report['violations'][0]['name']}).")
