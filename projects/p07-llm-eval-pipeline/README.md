# Project 07: Continuous LLM Evaluation Pipeline with Triad Metrics & Confidence Intervals

Automated test harness for continuous evaluation of Large Language Models (LLMs) and RAG applications, measuring Groundedness (Faithfulness), Answer Relevance, and Context Precision using synthetic test datasets, LLM-as-a-judge scoring, non-parametric bootstrap confidence intervals (95% CI), and CI/CD quality gate enforcement.

## Evaluation Metrics

1. **Groundedness / Faithfulness**:
   - Assesses what proportion of claims asserted in the LLM response are factually derived from the retrieved reference contexts.
   - Mitigates hallucinations and confabulation.

2. **Answer Relevance**:
   - Evaluates whether the generated response directly answers the core user inquiry without digression or omission.

3. **Context Precision@K**:
   - Evaluates the ranking quality of retrieved passages, rewarding systems that place relevant information at earlier ranks in the context window.

4. **Statistical Confidence Intervals**:
   - Runs $B=1,000$ non-parametric bootstrap iterations to compute standard error and 95% confidence intervals ($\text{CI}_{\text{lower}}, \text{CI}_{\text{upper}}$).
   - Prevents noisy, small-sample regressions from falsely tripping CI gates.

## Directory Structure

```
p07-llm-eval-pipeline/
├── evaluator/
│   ├── dataset.py
│   ├── harness.py
│   ├── judge.py
│   ├── metrics.py
│   └── statistics.py
├── README.md
├── requirements.txt
└── tests/
    └── test_eval_pipeline.py
```

## Running the Pytest Suite

```bash
PYTHONPATH=. pytest tests/ -v
```
