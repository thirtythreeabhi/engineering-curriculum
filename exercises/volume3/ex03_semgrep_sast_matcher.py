"""
Exercise 3.3: AST-Based Static Application Security Testing (SAST) Matcher

Problem:
Regex-based SAST tools suffer from high false-positive rates (matching inside comments
and docstrings) and miss multi-line or variable-tainted flows. Real SAST engines like
Semgrep parse source code into an Abstract Syntax Tree (AST) and walk AST nodes.

Implement an AST-based Python SAST scanner using `ast.parse` and `ast.NodeVisitor` that detects:
1. SQL injection via unparameterized query construction (`f-string`, `+`, `%`, `.format`,
   or intra-procedural tainted variables passed into `*.execute(...)`).
2. Insecure deserialization (`pickle.loads` / `pickle.load`, including import aliases).
3. Hardcoded credentials / secret keys (`ast.Assign` / `ast.AnnAssign` to string constants).
"""

import ast
from typing import Any, Dict, List, Set


SECRET_NAME_TOKENS = ("api_key", "secret_key", "jwt_secret", "password", "secret", "token")


class PythonSastVisitor(ast.NodeVisitor):
    def __init__(self, filename: str, source: str):
        self.filename = filename
        self.lines = source.splitlines()
        self.findings: List[Dict[str, Any]] = []
        self.pickle_module_aliases: Set[str] = set()
        self.pickle_load_aliases: Set[str] = set()
        # Intra-procedural set of variable names tainted by string interpolation/concat
        self.tainted_vars: Set[str] = set()

    def _add_finding(self, rule_id: str, severity: str, message: str, node: ast.AST) -> None:
        lineno = getattr(node, "lineno", 1)
        snippet = self.lines[lineno - 1].strip() if 0 < lineno <= len(self.lines) else ""
        self.findings.append({
            "rule_id": rule_id,
            "severity": severity,
            "message": message,
            "file": self.filename,
            "line": lineno,
            "match": snippet,
        })

    @staticmethod
    def _is_dynamic_sql_expr(node: ast.AST, tainted_vars: Set[str]) -> bool:
        if isinstance(node, ast.JoinedStr):
            return True
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
            return True
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format"
        ):
            return True
        if isinstance(node, ast.Name) and node.id in tainted_vars:
            return True
        return False

    @staticmethod
    def _is_secret_var_name(name: str) -> bool:
        lower = name.lower()
        return any(tok in lower for tok in SECRET_NAME_TOKENS)

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            if alias.name == "pickle":
                self.pickle_module_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "pickle":
            for alias in node.names:
                if alias.name in ("load", "loads"):
                    self.pickle_load_aliases.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        saved_taint = set(self.tainted_vars)
        self.tainted_vars = set()
        self.generic_visit(node)
        self.tainted_vars = saved_taint

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        saved_taint = set(self.tainted_vars)
        self.tainted_vars = set()
        self.generic_visit(node)
        self.tainted_vars = saved_taint

    def visit_Assign(self, node: ast.Assign) -> None:
        is_dynamic_str = self._is_dynamic_sql_expr(node.value, self.tainted_vars)
        for target in node.targets:
            if isinstance(target, ast.Name):
                if is_dynamic_str:
                    self.tainted_vars.add(target.id)
                else:
                    self.tainted_vars.discard(target.id)

                if (
                    self._is_secret_var_name(target.id)
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                    and len(node.value.value) >= 16
                ):
                    self._add_finding(
                        "hardcoded-secret",
                        "HIGH",
                        f"Hardcoded secret literal assigned to '{target.id}'",
                        node,
                    )
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name) and node.value is not None:
            if (
                self._is_secret_var_name(node.target.id)
                and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)
                and len(node.value.value) >= 16
            ):
                self._add_finding(
                    "hardcoded-secret",
                    "HIGH",
                    f"Hardcoded secret literal assigned to '{node.target.id}'",
                    node,
                )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # 1. SQLi detection on *.execute(query, ...)
        if isinstance(node.func, ast.Attribute) and node.func.attr == "execute" and node.args:
            first_arg = node.args[0]
            if self._is_dynamic_sql_expr(first_arg, self.tainted_vars):
                self._add_finding(
                    "sqli-ast-unparameterized",
                    "ERROR",
                    "Potential SQL Injection: dynamic string construction passed to .execute()",
                    node,
                )

        # 2. Insecure pickle deserialization (handles import aliases)
        if (
            isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id in self.pickle_module_aliases
            and node.func.attr in ("load", "loads")
        ) or (isinstance(node.func, ast.Name) and node.func.id in self.pickle_load_aliases):
            self._add_finding(
                "insecure-pickle",
                "CRITICAL",
                "Insecure Deserialization: pickle.load(s) allows arbitrary code execution",
                node,
            )

        self.generic_visit(node)


class SastEngine:
    def scan(self, filename: str, code: str) -> List[Dict[str, Any]]:
        tree = ast.parse(code, filename=filename)
        visitor = PythonSastVisitor(filename, code)
        visitor.visit(tree)
        return visitor.findings


if __name__ == "__main__":
    print("==> Running Exercise 3.3: AST-Based SAST Matcher...")

    vulnerable_code = """
import os
import pickle as pk
import sqlite3

def get_user_direct(cursor, username):
    # Vulnerability 1a: Direct f-string SQL Injection
    cursor.execute(f"SELECT * FROM users WHERE name = '{username}'")

def get_user_tainted(cursor, username):
    # Vulnerability 1b: Multi-line tainted query variable
    sql = "SELECT * FROM users WHERE name = '" + username + "'"
    cursor.execute(sql)

def load_session(data):
    # Vulnerability 2: Insecure Deserialization via aliased import
    return pk.loads(data)

# Vulnerability 3: Hardcoded secret
jwt_secret = "super_insecure_hardcoded_jwt_token_12345"

def safe_patterns(cursor, username):
    # Safe parameterized query (must NOT trigger)
    cursor.execute("SELECT * FROM users WHERE name = ?", (username,))
    # Safe env secret lookup (must NOT trigger)
    api_key = os.getenv("API_KEY")
    # Comment mentioning pickle.loads("fake") and jwt_secret = "abcdef1234567890abcd" (must NOT trigger)
    return api_key
"""

    scanner = SastEngine()
    findings = scanner.scan("vulnerable_app.py", vulnerable_code)

    assert len(findings) == 4, f"Expected 4 findings, got {len(findings)}: {findings}"
    rule_ids = [f["rule_id"] for f in findings]
    assert rule_ids.count("sqli-ast-unparameterized") == 2
    assert rule_ids.count("insecure-pickle") == 1
    assert rule_ids.count("hardcoded-secret") == 1
    assert all(f["line"] < 23 for f in findings), "Safe patterns & comments must produce zero false positives!"

    print(f"[PASS] Exercise 3.3 verified (AST SAST detected {len(findings)} vulnerabilities with 0 false positives).")
