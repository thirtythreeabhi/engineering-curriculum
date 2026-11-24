"""Pytest test suite for continuous LLM evaluation pipeline."""

import pytest
from evaluator.dataset import EvalSample, get_default_evaluation_dataset
from evaluator.harness import ContinuousEvalHarness
from evaluator.metrics import (
    calculate_answer_relevance,
    calculate_context_precision,
    calculate_groundedness,
)
from evaluator.statistics import compute_bootstrap_confidence_interval


def test_groundedness_faithfulness():
    contexts = [
        "Kubernetes pods are scheduled by kube-scheduler onto worker nodes.",
        "The kubelet agent runs on every node to maintain container health.",
    ]
    # Fully grounded claims
    grounded_claims = [
        "kube-scheduler schedules pods onto worker nodes.",
        "The kubelet agent runs on every node.",
    ]
    assert calculate_groundedness(grounded_claims, contexts) == 1.0

    # Hallucinated / unsupported claims
    hallucinated_claims = [
        "kube-scheduler schedules pods onto worker nodes.",
        "Kubernetes uses quantum entanglement to synchronize etcd clusters.",
    ]
    assert calculate_groundedness(hallucinated_claims, contexts) == 0.5


def test_answer_relevance():
    query = "What is the role of an API Gateway in microservices?"
    good_response = "An API Gateway routes incoming client traffic for microservices, enforces authentication, and provides rate limiting."
    assert calculate_answer_relevance(query, good_response) >= 0.70

    irrelevant_response = "The capital of France is Paris and it has a famous tower."
    assert calculate_answer_relevance(query, irrelevant_response) <= 0.20


def test_context_precision_rank_discounting():
    gt = "PostgreSQL WAL write-ahead logging guarantees durability."
    relevant_ctx = "PostgreSQL writes changes to the WAL (write-ahead log) before modifying data pages to guarantee durability."
    noise_ctx_1 = "Python was created by Guido van Rossum in the late 1980s."
    noise_ctx_2 = "HTML5 introduced native video and audio embedding tags."

    # High precision: relevant chunk is at rank 1
    high_rank_precision = calculate_context_precision([relevant_ctx, noise_ctx_1, noise_ctx_2], gt)

    # Low precision: relevant chunk is buried at rank 3
    low_rank_precision = calculate_context_precision([noise_ctx_1, noise_ctx_2, relevant_ctx], gt)

    assert high_rank_precision > low_rank_precision
    assert high_rank_precision == 1.0


def test_bootstrap_confidence_interval():
    scores = [0.85, 0.90, 0.88, 0.92, 0.87, 0.89, 0.91]
    ci = compute_bootstrap_confidence_interval(scores, n_bootstrap=500)
    assert 0.85 <= ci["mean"] <= 0.92
    assert ci["ci_lower"] <= ci["mean"] <= ci["ci_upper"]
    assert ci["std_err"] > 0.0


def test_eval_harness_ci_cd_gate():
    harness = ContinuousEvalHarness(
        groundedness_threshold=0.75,
        relevance_threshold=0.60,
        precision_threshold=0.60,
    )
    report = harness.run_eval()

    assert report["status"] == "PASSED"
    assert report["gate_checks"]["groundedness_passed"] is True
    assert report["gate_checks"]["relevance_passed"] is True
    assert report["gate_checks"]["precision_passed"] is True


def test_eval_harness_catches_regression():
    # Inject a hallucinated sample to test regression gate tripping
    hallucinated_sample = EvalSample(
        sample_id="hallucinated_01",
        query="What database does Kubernetes use?",
        contexts=["Kubernetes stores all cluster data in the etcd key-value store."],
        response="Kubernetes stores all cluster state in a distributed Cassandra cluster with MongoDB secondary indexing.",
        ground_truth="Kubernetes stores cluster data in etcd.",
        claims=[
            "Kubernetes stores state in Cassandra.",
            "It uses MongoDB secondary indexing.",
        ],
    )
    strict_harness = ContinuousEvalHarness(groundedness_threshold=0.90)
    report = strict_harness.run_eval([hallucinated_sample])
    assert report["status"] == "FAILED"
    assert report["gate_checks"]["groundedness_passed"] is False
