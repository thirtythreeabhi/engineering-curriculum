"""Pytest test suite validating CI/CD pipeline definitions and execution."""

import json
import os
import yaml
import pytest
from scripts.simulate_pipeline import run_full_pipeline

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


def test_workflow_yaml_validity_and_jobs():
    workflow_path = os.path.join(ROOT_DIR, ".github/workflows/production-pipeline.yml")
    assert os.path.isfile(workflow_path), "Workflow file must exist"

    with open(workflow_path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    assert "jobs" in doc
    jobs = doc["jobs"]

    expected_jobs = [
        "lint-and-format",
        "test",
        "sast-semgrep",
        "container-scan-trivy",
        "sbom-syft",
        "canary-deploy",
    ]
    for ej in expected_jobs:
        assert ej in jobs, f"Pipeline must define job: {ej}"

    # Canary deploy must depend on SAST, container scanning, and SBOM
    canary_needs = jobs["canary-deploy"]["needs"]
    assert "sast-semgrep" in canary_needs
    assert "container-scan-trivy" in canary_needs
    assert "sbom-syft" in canary_needs


def test_semgrep_security_rules_structure():
    rule_path = os.path.join(ROOT_DIR, ".semgrep.yml")
    assert os.path.isfile(rule_path)

    with open(rule_path, "r", encoding="utf-8") as f:
        doc = yaml.safe_load(f)

    rules = doc.get("rules", [])
    assert len(rules) >= 4

    rule_ids = [r["id"] for r in rules]
    assert "python-sqli-string-concat" in rule_ids
    assert "hardcoded-jwt-secret" in rule_ids
    assert "insecure-pickle-deserialization" in rule_ids
    assert "insecure-yaml-unsafe-load" in rule_ids


def test_full_pipeline_simulation_and_sbom_generation():
    success = run_full_pipeline()
    assert success is True

    sbom_path = os.path.join(ROOT_DIR, "app-sbom.spdx.json")
    assert os.path.isfile(sbom_path), "SBOM artifact must be created"

    with open(sbom_path, "r") as f:
        sbom = json.load(f)

    assert sbom["spdxVersion"] == "SPDX-2.3"
    assert len(sbom["packages"]) >= 3
    assert any(p["name"] == "fastapi" for p in sbom["packages"])
