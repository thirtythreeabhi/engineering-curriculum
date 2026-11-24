#!/usr/bin/env bash
set -e

echo "================================================================="
echo " RUNNING ALL ENGINEERING CURRICULUM EXERCISES (VOLUMES 1 TO 5) "
echo "================================================================="

EX_DIR="/home/abhi/engineering-curriculum/exercises"

echo ""
echo "--- [Volume 1: Backend Engineering Exercises] ---"
php "$EX_DIR/volume1/ex01_php_cow_zval.php"
php "$EX_DIR/volume1/ex02_php_pdo_prepared_transactions.php"
python3 "$EX_DIR/volume1/ex03_python_asyncio_event_loop.py"
python3 -c "import sqlite3; conn = sqlite3.connect(':memory:'); conn.executescript(open('$EX_DIR/volume1/ex04_sql_mvcc_isolation.sql').read()); print('[PASS] Exercise 1.4 verified (SQL transactions & solvency constraint passed).')"
python3 "$EX_DIR/volume1/ex05_jwt_timing_safe_verifier.py"

echo ""
echo "--- [Volume 2: AI Engineering Exercises] ---"
python3 "$EX_DIR/volume2/ex01_vector_math_cosine.py"
python3 "$EX_DIR/volume2/ex02_bm25_tf_idf_search.py"
python3 "$EX_DIR/volume2/ex03_reciprocal_rank_fusion.py"
python3 "$EX_DIR/volume2/ex04_agent_state_reducer.py"
python3 "$EX_DIR/volume2/ex05_rag_triad_evaluator.py"

echo ""
echo "--- [Volume 3: Cloud & DevSecOps Exercises] ---"
python3 "$EX_DIR/volume3/ex01_azure_rbac_least_privilege.py"
python3 "$EX_DIR/volume3/ex02_terraform_dag_resolver.py"
python3 "$EX_DIR/volume3/ex03_semgrep_sast_matcher.py"
python3 "$EX_DIR/volume3/ex04_spdx_sbom_parser.py"

echo ""
echo "--- [Volume 4: Distributed Systems Exercises] ---"
python3 "$EX_DIR/volume4/ex01_vector_clocks.py"
python3 "$EX_DIR/volume4/ex02_raft_election_sim.py"
python3 "$EX_DIR/volume4/ex03_outbox_pattern_relay.py"
python3 "$EX_DIR/volume4/ex04_distributed_lock_fencing.py"
python3 "$EX_DIR/volume4/ex05_circuit_breaker.py"

echo ""
echo "--- [Volume 5: Software Architecture & Economics Exercises] ---"
python3 "$EX_DIR/volume5/ex01_slo_error_budget_burn.py"
python3 "$EX_DIR/volume5/ex02_llm_inference_memory_math.py"
python3 "$EX_DIR/volume5/ex03_c4_model_validator.py"
python3 "$EX_DIR/volume5/ex04_cloud_finops_optimizer.py"

echo ""
echo "================================================================="
echo " ALL 23 EXERCISES COMPLETED AND VERIFIED SUCCESSFULLY: 100% PASS "
echo "================================================================="
