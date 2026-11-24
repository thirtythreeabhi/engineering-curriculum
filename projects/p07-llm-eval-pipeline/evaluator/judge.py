"""LLM-as-a-judge scoring engine with few-shot rubrics and structured output."""

from typing import Dict
from evaluator.dataset import EvalSample
from evaluator.metrics import (
    calculate_answer_relevance,
    calculate_context_precision,
    calculate_groundedness,
)


class LLMAsAJudge:
    def __init__(self, model_name: str = "mock-judge-v1"):
        self.model_name = model_name

    def evaluate_sample(self, sample: EvalSample) -> Dict[str, float]:
        """
        Evaluates a single sample across the triad metrics:
        - groundedness
        - answer_relevance
        - context_precision
        """
        groundedness = calculate_groundedness(sample.claims, sample.contexts)
        relevance = calculate_answer_relevance(sample.query, sample.response)
        precision = calculate_context_precision(sample.contexts, sample.ground_truth)

        # Harmonic mean (Composite Score)
        composite = (
            3.0 / (1.0 / max(0.01, groundedness) + 1.0 / max(0.01, relevance) + 1.0 / max(0.01, precision))
        )

        return {
            "groundedness": groundedness,
            "answer_relevance": relevance,
            "context_precision": precision,
            "composite_score": round(composite, 4),
        }
