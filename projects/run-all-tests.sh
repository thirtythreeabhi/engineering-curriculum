#!/usr/bin/env bash
set -e

PROJECTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURRICULUM_ROOT="$(dirname "$PROJECTS_DIR")"

echo "=========================================================================="
echo "    MODERN ENGINEERING CURRICULUM: MASTER PROJECTS TEST RUNNER            "
echo "=========================================================================="
echo "Workspace: $PROJECTS_DIR"
echo "Date: $(date -u)"
echo ""

declare -a PROJECTS=(
  "p01-php-db-integration:PHP 8.3 PDO E-Commerce Transactions:php $PROJECTS_DIR/p01-php-db-integration/tests/run_tests.php"
  "p02-php-webhook-receiver:PHP 8.3 Webhook Receiver & Replay Defense:php $PROJECTS_DIR/p02-php-webhook-receiver/tests/run_tests.php"
  "p03-python-fastapi-api:FastAPI Microservice (Pydantic v2 & JWT):PYTHONPATH=$PROJECTS_DIR/p03-python-fastapi-api pytest $PROJECTS_DIR/p03-python-fastapi-api/tests -q"
  "p04-async-db-sqlalchemy:Async SQLAlchemy 2.0 with Batched Upserts:PYTHONPATH=$PROJECTS_DIR/p04-async-db-sqlalchemy pytest $PROJECTS_DIR/p04-async-db-sqlalchemy/tests -q"
  "p05-langgraph-agent-state:LangGraph Agent with HITL Interruption:PYTHONPATH=$PROJECTS_DIR/p05-langgraph-agent-state pytest $PROJECTS_DIR/p05-langgraph-agent-state/tests -q"
  "p06-rag-hybrid-rerank:Hybrid RAG (Dense + BM25 + RRF + Cross-Encoder):PYTHONPATH=$PROJECTS_DIR/p06-rag-hybrid-rerank pytest $PROJECTS_DIR/p06-rag-hybrid-rerank/tests -q"
  "p07-llm-eval-pipeline:Continuous LLM Evaluation Test Harness:PYTHONPATH=$PROJECTS_DIR/p07-llm-eval-pipeline pytest $PROJECTS_DIR/p07-llm-eval-pipeline/tests -q"
  "p08-azure-secure-app:Azure App (Managed Identity & Private Link):PYTHONPATH=$PROJECTS_DIR/p08-azure-secure-app pytest $PROJECTS_DIR/p08-azure-secure-app/tests -q"
  "p09-terraform-infrastructure:Modular Terraform (VNet, NSG, AKS, State Lock):PYTHONPATH=$PROJECTS_DIR/p09-terraform-infrastructure pytest $PROJECTS_DIR/p09-terraform-infrastructure/tests -q"
  "p10-cicd-security-pipeline:DevSecOps CI/CD (Semgrep, Trivy, Syft, Canary):PYTHONPATH=$PROJECTS_DIR/p10-cicd-security-pipeline pytest $PROJECTS_DIR/p10-cicd-security-pipeline/tests -q"
  "p11-event-driven-microservices:Transactional Outbox + CDC + Kafka Consumer:PYTHONPATH=$PROJECTS_DIR/p11-event-driven-microservices pytest $PROJECTS_DIR/p11-event-driven-microservices/tests -q"
  "p12-end-to-end-platform:End-to-End Enterprise Architecture Platform:PYTHONPATH=$PROJECTS_DIR/p12-end-to-end-platform pytest $PROJECTS_DIR/p12-end-to-end-platform/tests -q"
)

TOTAL_COUNT=${#PROJECTS[@]}
PASSED_COUNT=0
FAILED_COUNT=0

for item in "${PROJECTS[@]}"; do
  IFS=":" read -r p_id p_desc p_cmd <<< "$item"
  echo "--------------------------------------------------------------------------"
  echo "=> Running Project: [$p_id] $p_desc"
  echo "   Command: $p_cmd"
  
  START_TIME=$(date +%s%N)
  if eval "$p_cmd"; then
    END_TIME=$(date +%s%N)
    DURATION=$(( (END_TIME - START_TIME) / 1000000 ))
    echo "   Status: [PASS] (${DURATION}ms)"
    PASSED_COUNT=$((PASSED_COUNT + 1))
  else
    END_TIME=$(date +%s%N)
    DURATION=$(( (END_TIME - START_TIME) / 1000000 ))
    echo "   Status: [FAIL] (${DURATION}ms)"
    FAILED_COUNT=$((FAILED_COUNT + 1))
  fi
done

echo ""
echo "=========================================================================="
echo "                       FINAL VERIFICATION SUMMARY                         "
echo "=========================================================================="
echo " Total Projects Tested: $TOTAL_COUNT"
echo " Passed:                $PASSED_COUNT / $TOTAL_COUNT"
echo " Failed:                $FAILED_COUNT / $TOTAL_COUNT"

if [ "$FAILED_COUNT" -eq 0 ]; then
  echo " Result:                ALL 12 PROJECTS PASSED WITH 100% SUCCESS!"
  echo "=========================================================================="
  exit 0
else
  echo " Result:                SOME PROJECTS FAILED VERIFICATION."
  echo "=========================================================================="
  exit 1
fi
