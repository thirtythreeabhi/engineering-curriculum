"""
Exercise 3.3: Static Application Security Testing (SAST) Rule Matcher

Problem:
Implement a lightweight SAST scanner that parses code files and detects
security anti-patterns based on declarative rule definitions (similar to Semgrep):
1. SQL injection via string formatting or f-strings.
2. Insecure deserialization (e.g. pickle.loads).
3. Hardcoded credentials / secret keys.
"""

import re
from typing import Dict, List, Tuple


class SastEngine:
    def __init__(self, rules: List[Dict[str, str]]):
        self.rules = rules

    def scan(self, filename: str, code: str) -> List[Dict[str, any]]:
        findings = []
        lines = code.splitlines()

        for rule in self.rules:
            pattern = re.compile(rule["regex"])
            for line_no, line in enumerate(lines, start=1):
                if pattern.search(line):
                    findings.append({
                        "rule_id": rule["id"],
                        "severity": rule["severity"],
                        "message": rule["message"],
                        "file": filename,
                        "line": line_no,
                        "match": line.strip(),
                    })

        return findings


if __name__ == "__main__":
    print("==> Running Exercise 3.3: SAST Rule Matcher...")
    rules = [
        {
            "id": "sqli-fstring",
            "regex": r"(cursor|session)\.execute\(f[\"'].*SELECT.*\{",
            "severity": "ERROR",
            "message": "Potential SQL Injection: unparameterized query using f-string interpolation",
        },
        {
            "id": "insecure-pickle",
            "regex": r"pickle\.loads\(",
            "severity": "CRITICAL",
            "message": "Insecure Deserialization: pickle.loads allows arbitrary remote code execution",
        },
        {
            "id": "hardcoded-secret",
            "regex": r"(api_key|secret_key|jwt_secret)\s*=\s*[\"'][a-zA-Z0-9_\-]{16,}[\"']",
            "severity": "HIGH",
            "message": "Hardcoded secret key detected in source code",
        },
    ]

    vulnerable_code = """
import pickle
import sqlite3

def get_user(cursor, username):
    # Vulnerability 1: SQL Injection
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")

def load_session(data):
    # Vulnerability 2: Insecure Deserialization
    return pickle.loads(data)

# Vulnerability 3: Hardcoded secret
jwt_secret = "super_insecure_hardcoded_jwt_token_12345"
"""

    scanner = SastEngine(rules)
    findings = scanner.scan("vulnerable_app.py", vulnerable_code)

    assert len(findings) == 3
    rule_ids = {f["rule_id"] for f in findings}
    assert rule_ids == {"sqli-fstring", "insecure-pickle", "hardcoded-secret"}
    print(f"[PASS] Exercise 3.3 verified (Detected {len(findings)} security vulnerabilities).")
