"""Triad RAG evaluation metrics: Groundedness, Answer Relevance, Context Precision."""

import re
from typing import List


def extract_key_tokens(text: str) -> set[str]:
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "to", "in", "for", "of",
        "and", "or", "by", "with", "that", "this", "what", "how", "why", "role", "does"
    }
    raw = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
    tokens = set()
    for w in raw:
        if w in stop_words:
            continue
        if w.endswith("s") and len(w) > 3 and not w.endswith("ss"):
            tokens.add(w[:-1])
        tokens.add(w)
    return tokens


def calculate_groundedness(claims: List[str], contexts: List[str]) -> float:
    """
    Computes Groundedness / Faithfulness:
    Fraction of claims made in the LLM response that are directly supported by the context.
    Score in [0.0, 1.0].
    """
    if not claims:
        return 1.0

    unified_context = " ".join(contexts).lower()
    supported_count = 0

    for claim in claims:
        claim_tokens = extract_key_tokens(claim)
        if not claim_tokens:
            continue
        matched = sum(1 for tok in claim_tokens if tok in unified_context)
        if (matched / len(claim_tokens)) >= 0.40:
            supported_count += 1

    return round(supported_count / max(1, len(claims)), 4)


def calculate_answer_relevance(query: str, response: str) -> float:
    """
    Computes Answer Relevance:
    Measures semantic topic alignment between query and response.
    Score in [0.0, 1.0].
    """
    query_tokens = extract_key_tokens(query)
    response_tokens = extract_key_tokens(response)

    if not query_tokens:
        return 1.0

    intersection = query_tokens.intersection(response_tokens)
    recall = len(intersection) / len(query_tokens)

    words_count = len(response.split())
    if words_count < 3:
        return 0.0

    return round(min(1.0, recall), 4)


def calculate_context_precision(contexts: List[str], ground_truth: str) -> float:
    """
    Computes Context Precision@K:
    Rewards contexts containing the target information appearing at higher ranks.
    Precision@K = sum(Precision@k * v_k) / total_relevant_contexts
    """
    if not contexts:
        return 0.0

    gt_tokens = extract_key_tokens(ground_truth)
    if not gt_tokens:
        return 1.0

    relevant_indicator: List[int] = []
    precisions_at_k: List[float] = []
    cumulative_relevant = 0

    for k, ctx in enumerate(contexts, start=1):
        ctx_tokens = extract_key_tokens(ctx)
        overlap = len(gt_tokens.intersection(ctx_tokens))
        # Context is relevant if it contains at least 50% of the ground truth tokens
        is_relevant = 1 if (overlap / max(1, len(gt_tokens))) >= 0.40 else 0
        relevant_indicator.append(is_relevant)

        if is_relevant:
            cumulative_relevant += 1

        precisions_at_k.append(cumulative_relevant / k)

    total_relevant = sum(relevant_indicator)
    if total_relevant == 0:
        return 0.0

    weighted_precision_sum = sum(
        p * v for p, v in zip(precisions_at_k, relevant_indicator)
    )
    return round(weighted_precision_sum / total_relevant, 4)
