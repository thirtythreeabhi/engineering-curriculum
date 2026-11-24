"""
Exercise 2.5: Continuous RAG Evaluation Triad Metrics (Deterministic Lexical + Negation-Aware)

Problem:
Compute the core Ragas / TruLens triad metrics in a deterministic offline harness:
1. Groundedness (Faithfulness): Are claims lexically supported by the reference context
   WITHOUT polarity contradiction (e.g., "not"/"never"/"no" flipping a true statement)?
2. Answer Relevance: Does the generated answer address the user query?
3. Context Precision@K: Are relevant contexts retrieved at the highest ranks?

Note on scope:
In production, Groundedness and Answer Relevance are typically scored by an LLM-as-a-judge
or NLI cross-encoder. Here we implement a deterministic, zero-network lexical + negation-cue
baseline suitable for offline unit tests—explicitly using whole-word token matching (no
substring false positives) and polarity checks (so negated claims do not score 1.0).
"""

import re
from typing import Dict, List, Set

STOPWORDS: Set[str] = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "to", "in", "for", "of", "and", "or", "by", "with", "that", "this",
    "it", "its", "what", "how", "why", "from", "on", "as", "at",
}

NEGATION_CUES: Set[str] = {
    "not", "never", "no", "none", "neither", "nor", "without",
    "cannot", "can't", "isn't", "aren't", "wasn't", "weren't",
    "doesn't", "don't", "didn't", "won't", "wouldn't", "shouldn't",
}


def tokenize_content(text: str) -> Set[str]:
    """Extracts whole-word content tokens (lowercase), excluding stopwords and negation cues."""
    raw = re.findall(r"\b[a-z0-9\-']+\b", text.lower())
    tokens: Set[str] = set()
    for tok in raw:
        if tok in STOPWORDS or tok in NEGATION_CUES:
            continue
        tokens.add(tok)
    return tokens


def has_odd_negation(text: str) -> bool:
    """Returns True when text contains an odd number of explicit negation cues."""
    raw = re.findall(r"\b[a-z0-9\-']+\b", text.lower())
    neg_count = sum(1 for tok in raw if tok in NEGATION_CUES)
    return (neg_count % 2) == 1


def _split_sentences(contexts: List[str]) -> List[str]:
    sentences: List[str] = []
    for ctx in contexts:
        for part in re.split(r"[.!?\n]+", ctx):
            stripped = part.strip()
            if stripped:
                sentences.append(stripped)
    return sentences


def evaluate_rag_triad(
    query: str,
    contexts: List[str],
    response: str,
    claims: List[str],
    ground_truth_keywords: List[str],
) -> Dict[str, float]:
    # 1. Groundedness (whole-word overlap against best sentence + negation polarity check)
    context_sentences = _split_sentences(contexts)
    sentence_data = [
        (tokenize_content(sent), has_odd_negation(sent))
        for sent in context_sentences
    ]

    supported = 0
    for claim in claims:
        c_tokens = tokenize_content(claim)
        c_neg = has_odd_negation(claim)
        if not c_tokens:
            continue

        best_overlap = 0.0
        best_sent_neg = False
        for s_tokens, s_neg in sentence_data:
            overlap = len(c_tokens.intersection(s_tokens)) / len(c_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
                best_sent_neg = s_neg

        if best_overlap >= 0.5 and c_neg == best_sent_neg:
            supported += 1

    groundedness = supported / max(1, len(claims)) if claims else 1.0

    # 2. Answer Relevance (whole-word content token recall)
    q_words = tokenize_content(query)
    r_words = tokenize_content(response)
    relevance = len(q_words.intersection(r_words)) / max(1, len(q_words)) if q_words else 1.0

    # 3. Context Precision@K
    gt_set = {k.lower() for k in ground_truth_keywords}
    cumulative_hits = 0
    precisions: List[float] = []
    indicators: List[int] = []

    for k, ctx in enumerate(contexts, start=1):
        ctx_tokens = set(re.findall(r"\b[a-z0-9\-']+\b", ctx.lower()))
        is_hit = 1 if len(gt_set.intersection(ctx_tokens)) > 0 else 0
        indicators.append(is_hit)
        if is_hit:
            cumulative_hits += 1
        precisions.append(cumulative_hits / k)

    total_hits = sum(indicators)
    precision_at_k = (
        sum(p * v for p, v in zip(precisions, indicators)) / total_hits
        if total_hits > 0
        else 0.0
    )

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

    # Negated / contradicted claims must NOT score grounded = 1.0
    negated_claims = [
        "Raft is not designed for understandability.",
        "It never provides leader-based replicated state machines.",
    ]
    neg_scores = evaluate_rag_triad(query, contexts, response, negated_claims, gt_keywords)
    assert neg_scores["groundedness"] == 0.0, (
        f"Negated claims must score 0.0 groundedness, got {neg_scores['groundedness']}"
    )

    # Substring trap: "cat" must not match "category"
    # (Under naive substring overlap, "cat" in "category" + "items" would score 2/3 >= 0.5 -> 1.0!)
    trap_scores = evaluate_rag_triad(
        "What does the cat eat?",
        ["The category contains items."],
        "A cat eats items.",
        ["A cat eats items."],
        ["cat"],
    )
    assert trap_scores["groundedness"] == 0.0
    assert trap_scores["context_precision"] == 0.0

    print(
        f"[PASS] Exercise 2.5 verified "
        f"(Groundedness={scores['groundedness']}, Negated={neg_scores['groundedness']}, "
        f"Relevance={scores['answer_relevance']}, Precision={scores['context_precision']})."
    )
