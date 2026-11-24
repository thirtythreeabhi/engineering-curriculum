"""
Exercise 3.4: SPDX 2.3 Software Bill of Materials (SBOM) Analyzer

Problem:
Implement an automated SBOM license auditor that:
1. Parses standard SPDX-2.3 JSON documents.
2. Evaluates both simple SPDX identifiers ("MIT", "GPL-3.0-only") and compound
   SPDX license expressions ("MIT OR Apache-2.0", "MIT AND BSD-3-Clause",
   "(MIT OR GPL-3.0-only) AND Apache-2.0", "Apache-2.0 WITH LLVM-exception").
3. Enforces an open-source license compliance policy.
"""

import json
import re
from typing import Any, Dict, List, Set


_TOKEN_RE = re.compile(r"\(|\)|\bAND\b|\bOR\b|\bWITH\b|[A-Za-z0-9.\-+]+")


class SpdxExpressionEvaluator:
    """Recursive-descent evaluator for SPDX license expressions."""

    def __init__(self, allowed_licenses: Set[str]):
        self.allowed = allowed_licenses

    def is_compliant(self, expression: str) -> bool:
        tokens = _TOKEN_RE.findall(expression.strip())
        if not tokens:
            return False
        self._tokens = tokens
        self._pos = 0
        result = self._parse_or()
        if self._pos != len(self._tokens):
            return False
        return result

    def _peek(self) -> str | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _consume(self) -> str:
        tok = self._tokens[self._pos]
        self._pos += 1
        return tok

    def _parse_or(self) -> bool:
        left = self._parse_and()
        while self._peek() == "OR":
            self._consume()
            right = self._parse_and()
            left = left or right
        return left

    def _parse_and(self) -> bool:
        left = self._parse_atom()
        while self._peek() == "AND":
            self._consume()
            right = self._parse_atom()
            left = left and right
        return left

    def _parse_atom(self) -> bool:
        tok = self._peek()
        if tok == "(":
            self._consume()
            val = self._parse_or()
            if self._peek() == ")":
                self._consume()
            return val
        if tok is None or tok in (")", "AND", "OR", "WITH"):
            return False
        license_id = self._consume()
        if self._peek() == "WITH":
            self._consume()
            exception_id = self._consume() if self._peek() is not None else ""
            full_with = f"{license_id} WITH {exception_id}"
            return (full_with in self.allowed) or (license_id in self.allowed)
        return license_id in self.allowed


class SbomLicenseAuditor:
    def __init__(self, allowed_licenses: Set[str]):
        self.allowed_licenses = allowed_licenses
        self.evaluator = SpdxExpressionEvaluator(allowed_licenses)

    def audit_spdx(self, spdx_json_str: str) -> Dict[str, Any]:
        data = json.loads(spdx_json_str)
        packages = data.get("packages", [])

        compliant_packages: List[Dict[str, str]] = []
        violations: List[Dict[str, str]] = []

        for pkg in packages:
            name = pkg.get("name", "unknown")
            version = pkg.get("versionInfo", "unknown")
            license_str = pkg.get("licenseConcluded", "NOASSERTION")

            if self.evaluator.is_compliant(license_str):
                compliant_packages.append({"name": name, "version": version, "license": license_str})
            else:
                violations.append({
                    "name": name,
                    "version": version,
                    "license": license_str,
                    "reason": f"License expression '{license_str}' fails approved license policy.",
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

    # Test 1: Compound SPDX expression compliance checks
    assert auditor.evaluator.is_compliant("MIT OR Apache-2.0") is True
    assert auditor.evaluator.is_compliant("MIT OR GPL-3.0-only") is True   # Choice of MIT satisfies policy
    assert auditor.evaluator.is_compliant("MIT AND BSD-3-Clause") is True
    assert auditor.evaluator.is_compliant("MIT AND GPL-3.0-only") is False # Copyleft required by AND
    assert auditor.evaluator.is_compliant("(MIT OR GPL-3.0-only) AND Apache-2.0") is True
    assert auditor.evaluator.is_compliant("(MIT OR Apache-2.0) AND GPL-3.0-only") is False

    # Test 2: Full SPDX-2.3 document audit including compound expressions
    sample_sbom = """
    {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "enterprise-backend-service",
        "packages": [
            {"name": "fastapi", "versionInfo": "0.110.0", "licenseConcluded": "MIT"},
            {"name": "cryptography", "versionInfo": "42.0.0", "licenseConcluded": "Apache-2.0 OR BSD-3-Clause"},
            {"name": "dual-lib", "versionInfo": "2.1.0", "licenseConcluded": "MIT AND BSD-3-Clause"},
            {"name": "gpl-library", "versionInfo": "1.0.0", "licenseConcluded": "GPL-3.0-only"},
            {"name": "tainted-bundle", "versionInfo": "0.5.0", "licenseConcluded": "MIT AND GPL-3.0-only"}
        ]
    }
    """

    report = auditor.audit_spdx(sample_sbom)
    assert report["total_packages"] == 5
    assert report["compliant_count"] == 3
    assert report["violation_count"] == 2
    violators = [v["name"] for v in report["violations"]]
    assert violators == ["gpl-library", "tainted-bundle"]
    assert report["status"] == "NON_COMPLIANT"

    print(f"[PASS] Exercise 3.4 verified (Compound SPDX expressions & violations: {violators}).")
