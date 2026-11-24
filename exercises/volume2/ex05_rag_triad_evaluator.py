"""
Exercise 2.5: Continuous RAG Evaluation Triad Metrics

Problem:
Compute the core Ragas / TruLens triad metrics:
1. Groundedness (Faithfulness): Are all claims supported by reference context?
2. Answer Relevance: Does the generated answer address the user query?
3. Context Precision: Are relevant contexts retrieved at the highest ranks?
"""

from typing import List


def evaluate_rag_triad(
    query: str,
    contexts: List[str],
    response: str,
    claims: List[str],
    ground_truth_keywords: List[str],
) -> dict:
    # 1. Groundedness
    unified_context = " ".join(contexts).lower()
    supported = 0
    for claim in claims:
        words = [w.lower() for w in claim.split() if len(w) > 3]
        if words and sum(1 for w in words if w in unified_context) / len(words) >= 0.5:
            supported += 1
    groundedness = supported / max(1, len(claims))

    # 2. Answer Relevance
    q_words = set(w.lower() for w in query.split() if len(w) > 3)
    r_words = set(w.lower() for w in response.split() if len(w) > 3)
    relevance = len(q_words.intersection(r_words)) / max(1, len(q_words))

    # 3. Context Precision@K
    gt_set = set(k.lower() for k in ground_truth_keywords)
    cumulative_hits = 0
    precisions = []
    indicators = []

    for k, ctx in enumerate(contexts, start=1):
        ctx_words = set(ctx.lower().split())
        is_hit = 1 if len(gt_set.intersection(ctx_words)) > 0 else 0
        indicators.append(is_hit)
        if is_hit:
            cumulative_hits += 1
        precisions.append(cumulative_hits / k)

    total_hits = sum(indicators)
    precision_at_k = (sum(p * v for p, v in zip(precisions, indicators)) / total_hits) if total_hits > 0 else 0.0

    return {
        "groundedness": round(groundedness, 4),
        "answer_relevance": round(relevance, 4),
        "context_precision": round(precision_at_k, 4),
    }


if __name__ == "__main__":
    print("==> Running Exercise 2.5: RAG Triad Evaluator...")
    query = "What is the primary benefit of Raft consensus?"
    contexts = [
        "Raft is a consensus algorithm designed for understandability, providing strong leader-based replicated state machines.",
        "Paxos is historically another consensus algorithm created by Leslie Lamport.",
    ]
    response = "The primary benefit of Raft consensus is understandability and leader-based state machine replication."
    claims = [
        "Raft is designed for understandability.",
        "It provides leader-based replicated state machines.",
    ]
    gt_keywords = ["understandability", "leader-based"]

    scores = evaluate_rag_triad(query, contexts, response, claims, gt_keywords)

    assert scores["groundedness"] == 1.0
    assert scores["answer_relevance"] >= 0.60
    assert scores["context_precision"] == 1.0
    print(f"[PASS] Exercise 2.5 verified (Groundedness={scores['groundedness']}, Relevance={scores['answer_relevance']}, Precision={scores['context_precision']}).")
