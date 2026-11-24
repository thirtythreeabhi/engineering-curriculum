"""Continuous automated evaluation harness and CI/CD gate validator."""

from typing import Dict, List
from evaluator.dataset import EvalSample, get_default_evaluation_dataset
from evaluator.judge import LLMAsAJudge
from evaluator.statistics import compute_bootstrap_confidence_interval


class ContinuousEvalHarness:
    def __init__(
        self,
        groundedness_threshold: float = 0.85,
        relevance_threshold: float = 0.80,
        precision_threshold: float = 0.75,
    ):
        self.groundedness_threshold = groundedness_threshold
        self.relevance_threshold = relevance_threshold
        self.precision_threshold = precision_threshold
        self.judge = LLMAsAJudge()

    def run_eval(self, dataset: List[EvalSample] = None) -> Dict[str, any]:
        samples = dataset or get_default_evaluation_dataset()

        groundedness_scores: List[float] = []
        relevance_scores: List[float] = []
        precision_scores: List[float] = []
        composite_scores: List[float] = []
        detailed_results = []

        for sample in samples:
            res = self.judge.evaluate_sample(sample)
            groundedness_scores.append(res["groundedness"])
            relevance_scores.append(res["answer_relevance"])
            precision_scores.append(res["context_precision"])
            composite_scores.append(res["composite_score"])
            detailed_results.append({
                "sample_id": sample.sample_id,
                **res,
            })

        ci_groundedness = compute_bootstrap_confidence_interval(groundedness_scores)
        ci_relevance = compute_bootstrap_confidence_interval(relevance_scores)
        ci_precision = compute_bootstrap_confidence_interval(precision_scores)
        ci_composite = compute_bootstrap_confidence_interval(composite_scores)

        # Check CI/CD quality gate pass criteria
        passed_groundedness = ci_groundedness["mean"] >= self.groundedness_threshold
        passed_relevance = ci_relevance["mean"] >= self.relevance_threshold
        passed_precision = ci_precision["mean"] >= self.precision_threshold

        all_passed = passed_groundedness and passed_relevance and passed_precision

        return {
            "status": "PASSED" if all_passed else "FAILED",
            "total_samples": len(samples),
            "metrics": {
                "groundedness": ci_groundedness,
                "answer_relevance": ci_relevance,
                "context_precision": ci_precision,
                "composite": ci_composite,
            },
            "thresholds": {
                "groundedness": self.groundedness_threshold,
                "answer_relevance": self.relevance_threshold,
                "context_precision": self.precision_threshold,
            },
            "gate_checks": {
                "groundedness_passed": passed_groundedness,
                "relevance_passed": passed_relevance,
                "precision_passed": passed_precision,
            },
            "detailed_results": detailed_results,
        }
