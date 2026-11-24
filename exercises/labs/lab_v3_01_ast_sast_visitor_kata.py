"""
Lab V3-01 (Volume 3 Ch 7 - DevSecOps / SAST):
AST-Based SAST Visitor Starter Lab

Instructions:
Unlike regex scanners (which trigger false positives on comments and docstrings),
real SAST tools inspect the Python Abstract Syntax Tree (`ast.parse`).

Your task:
Complete the `TODO`s inside `StarterSastVisitor` so `scan()` detects:
1. `sqli-ast-unparameterized`: `*.execute(...)` whose first argument is an `ast.JoinedStr`
   (f-string) or `ast.BinOp` (`+` / `%`), WITHOUT flagging parameterized queries!
2. `insecure-pickle`: calls to `pickle.loads(...)` / `pickle.load(...)`.
3. `hardcoded-secret`: assignments to `jwt_secret` / `api_key` / `secret_key` with a
   string `ast.Constant` of length >= 16 (WITHOUT flagging `os.getenv(...)` or comments!).

Run this file directly to check your implementation:
    python3 exercises/labs/lab_v3_01_ast_sast_visitor_kata.py

Reference solution:
- exercises/volume3/ex03_semgrep_sast_matcher.py
"""

import ast
from typing import Any, Dict, List


class StarterSastVisitor(ast.NodeVisitor):
    def __init__(self):
        self.findings: List[Dict[str, Any]] = []

    def visit_Call(self, node: ast.Call) -> None:
        # TODO 1: Detect `*.execute(arg, ...)` where `arg` is `ast.JoinedStr` or `ast.BinOp`.
        #         Append {"rule_id": "sqli-ast-unparameterized", "line": node.lineno}.
        # TODO 2: Detect `pickle.loads(...)` / `pickle.load(...)`.
        #         Append {"rule_id": "insecure-pickle", "line": node.lineno}.
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        # TODO 3: Detect assignments where target `ast.Name.id` contains
        #         ("api_key", "secret_key", "jwt_secret") AND value is a string
        #         `ast.Constant` with len >= 16.
        #         Append {"rule_id": "hardcoded-secret", "line": node.lineno}.
        self.generic_visit(node)


def scan(code: str) -> List[Dict[str, Any]]:
    tree = ast.parse(code)
    visitor = StarterSastVisitor()
    visitor.visit(tree)
    return visitor.findings


if __name__ == "__main__":
    print("==> Running Lab V3-01: AST-Based SAST Visitor Lab...")
    sample = """
import os
import pickle

def handler(cursor, user):
    cursor.execute(f"SELECT * FROM users WHERE name = '{user}'")
    cursor.execute("SELECT * FROM users WHERE name = ?", (user,))  # Safe!
    return pickle.loads(b"payload")

jwt_secret = "hardcoded_production_secret_value_999"
api_key = os.getenv("API_KEY")  # Safe!
# pickle.loads("commented out") and jwt_secret = "commented_secret_123456"
"""
    results = scan(sample)
    rule_ids = [r["rule_id"] for r in results]
    assert rule_ids.count("sqli-ast-unparameterized") == 1, f"[FAIL] Expected 1 SQLi finding, got {results}"
    assert rule_ids.count("insecure-pickle") == 1, f"[FAIL] Expected 1 pickle finding, got {results}"
    assert rule_ids.count("hardcoded-secret") == 1, f"[FAIL] Expected 1 secret finding, got {results}"
    assert len(results) == 3, f"[FAIL] Unexpected extra findings (false positives?): {results}"

    print("[PASS] Lab V3-01 completed!")
