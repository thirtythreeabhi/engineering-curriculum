# Project 10: Production DevSecOps CI/CD Pipeline (SAST, Trivy, Syft SBOM, Canary Rollout)

Comprehensive GitHub Actions continuous integration and continuous deployment (CI/CD) pipeline codifying DevSecOps shift-left practices: automated linting, unit testing with code coverage gates, static application security testing (Semgrep SAST), container image vulnerability scanning (Trivy), Software Bill of Materials (SBOM) generation (Syft SPDX-2.3), and automated canary deployments with synthetic latency/error probes and automated rollback.

## Multi-Stage Pipeline Stages

1. **Lint & Code Style**:
   - Runs Ruff and Flake8 syntax linters to enforce clean code standards.

2. **Test & Coverage Gate**:
   - Executes Pytest with coverage analysis, failing if coverage drops below 80%.

3. **SAST Analysis (Semgrep)**:
   - Evaluates custom `.semgrep.yml` rules detecting SQL injection, hardcoded JWT secrets, insecure YAML deserialization, and pickle object injection. Exports SARIF reports.

4. **Container Image Scanning (Trivy)**:
   - Scans base OS images and application packages, failing the pipeline if unpatched `HIGH` or `CRITICAL` CVEs are discovered.

5. **SBOM Generation (Syft)**:
   - Generates an auditable Software Bill of Materials in standard SPDX 2.3 JSON format, cataloging dependencies and licenses.

6. **Automated Canary Deployment**:
   - Deploys canary to 10% traffic. Runs automated synthetic probes. Promotes to 100% on success or triggers immediate automated rollback if error rate > 0.1% or p95 latency > 150ms.

## Directory Structure

```
p10-cicd-security-pipeline/
├── .github/
│   └── workflows/
│       └── production-pipeline.yml
├── .semgrep.yml
├── README.md
├── requirements.txt
├── scripts/
│   ├── simulate_pipeline.py
│   └── verify_canary.py
└── tests/
    └── test_pipeline_definition.py
```

## Running the Verification Suite

```bash
PYTHONPATH=. pytest tests/ -v
```
