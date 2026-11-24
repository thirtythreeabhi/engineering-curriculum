# Hands-On Guided Labs & Debugging Katas (`exercises/labs/`)

Unlike the self-verifying reference exercises in `exercises/volume1/`–`exercises/volume5/`, every file in `exercises/labs/` is an **active coding starter or broken-code debugging kata**.

Each lab is deliberately broken or incomplete (`# BUG:` / `# TODO:`) and **fails its built-in assertions out-of-the-box** until you diagnose the root cause and implement the fix.

## Lab Index & Reference Mapping

| Lab File | Volume & Chapters | Skills Practiced | Reference Solution |
| :--- | :--- | :--- | :--- |
| `lab_v1_01_async_and_token_bucket_kata.py` | Vol I: Ch 2, Ch 5, Ch 7 | Non-blocking `asyncio.sleep`, token bucket refill math without starvation | `../volume1/ex03_python_asyncio_event_loop.py` |
| `lab_v1_02_jwt_alg_none_kata.py` | Vol I: Ch 6 | Rejecting `alg: none` / `RS256` key confusion, safe base64/JSON parsing | `../volume1/ex05_jwt_timing_safe_verifier.py` |
| `lab_v2_01_recursive_chunker_kata.py` | Vol II: Ch 2 | Recursive separator fallback, overlap window merging | *(Vol II Ch 2 text + inline assertions)* |
| `lab_v3_01_ast_sast_visitor_kata.py` | Vol III: Ch 7 | Writing an `ast.NodeVisitor` SAST scanner (zero comment false positives) | `../volume3/ex03_semgrep_sast_matcher.py` |
| `lab_v4_01_lock_fencing_and_breaker_kata.py` | Vol IV: Ch 7, Ch 9 | Lock lease TTL checks, resetting consecutive failure count on success | `../volume4/ex04_distributed_lock_fencing.py`, `../volume4/ex05_circuit_breaker.py` |
| `lab_v5_01_sli_and_kv_cache_kata.py` | Vol V: Ch 5, Ch 9 | Consistent SLI denominators (`<= 1.0`), GiB KV-cache sizing, `>8` GPU scaling | `../volume5/ex01_slo_error_budget_burn.py`, `../volume5/ex02_llm_inference_memory_math.py` |

## How to Work Through a Lab

1. **Run the lab first** to observe the failing assertion or unhandled exception:
   ```bash
   python3 exercises/labs/lab_v1_01_async_and_token_bucket_kata.py
   ```
2. **Read the `# BUG:` and `# TODO:` markers** in the lab file and trace the concrete test inputs at the bottom of the file.
3. **Edit the lab file** until all assertions pass (`[PASS] Lab ... completed!`).
4. **Compare your fix** against the corresponding reference implementation in `exercises/volume*/`.
