"""
Lab V5-01 (Volume 5 Ch 5 & Ch 9 - SLOs & AI Inference Economics):
SLI Formula >100% & KV Cache Unit-Mismatch Debugging Kata

Instructions:
This lab reproduces two real quantitative bugs audited in Volume 5:
  1. Part A (`compute_availability_sli`): Counts `2xx + 3xx + 4xx` (`status < 500`) in
     the numerator while excluding `4xx` from the denominator (`total - count_4xx`),
     allowing Availability SLI to exceed 1.0 (100%)!
  2. Part B (`estimate_kv_cache_gib` & `gpus_required`):
     - Omits the factor of `2` (Key + Value tensors) and divides by `10**9` instead of `1024**3`.
     - Crashes with `StopIteration` when `gpus_needed > 8`!

Your task:
- Fix `compute_availability_sli()` so valid client requests (`total - count_4xx`) or
  all requests are counted consistently in BOTH numerator and denominator (never > 1.0).
- Fix `estimate_kv_cache_gib()` (formula: `2 * n_layers * n_kv_heads * head_dim * bytes_per_param * batch * seq / 1024**3`).
- Implement `gpus_required()` handling both single-node `[1, 2, 4, 8]` and multi-node `> 8` (multiples of 8).

Run this file directly to check your fixes:
    python3 exercises/labs/lab_v5_01_sli_and_kv_cache_kata.py

Reference solutions:
- exercises/volume5/ex01_slo_error_budget_burn.py
- exercises/volume5/ex02_llm_inference_memory_math.py
"""

import math
from typing import List


def compute_availability_sli(total_requests: int, count_4xx: int, count_5xx: int) -> float:
    # BUG: Numerator includes 4xx (total - count_5xx), while denominator excludes 4xx!
    # When count_4xx > count_5xx, this returns > 1.0 (e.g. 111.1% availability)!
    # TODO: Exclude 4xx from BOTH numerator and denominator (good = valid - count_5xx, valid = total - count_4xx).
    good_requests = total_requests - count_5xx
    valid_requests = total_requests - count_4xx
    return good_requests / max(1, valid_requests)


def estimate_kv_cache_gib(
    batch_size: int,
    context_tokens: int,
    n_layers: int = 80,
    n_kv_heads: int = 8,
    head_dim: int = 128,
    bytes_per_param: int = 2,
) -> float:
    # BUG 1: Missing factor of 2 (Key + Value)!
    # BUG 2: Divides by 10**9 (decimal GB) instead of 1024**3 (binary GiB)!
    kv_bytes = n_layers * n_kv_heads * head_dim * bytes_per_param * batch_size * context_tokens
    return kv_bytes / (10**9)


def gpus_required(total_vram_gib: float, gpu_vram_gib: float = 80.0) -> int:
    gpus_needed = max(1, math.ceil(total_vram_gib / gpu_vram_gib))
    tp_sizes: List[int] = [1, 2, 4, 8]
    # BUG: Raises StopIteration when gpus_needed > 8!
    # TODO: For gpus_needed > 8, scale in 8-GPU multi-node increments (16, 24, ...).
    return next(tp for tp in tp_sizes if tp >= gpus_needed)


if __name__ == "__main__":
    print("==> Running Lab V5-01: SLI & KV Cache Math Kata...")

    # Verify Part A: 1000 requests, 100 client 4xx errors, 9 server 5xx errors -> valid=900, good=891 -> 0.99
    sli = compute_availability_sli(total_requests=1000, count_4xx=100, count_5xx=9)
    assert 0.0 <= sli <= 1.0, f"[FAIL Part A] SLI exceeded 100%: {sli}"
    assert abs(sli - 0.99) < 1e-9, f"[FAIL Part A] Expected 0.99, got {sli}"

    # Verify Part B: 32 users * 4096 tokens on LLaMA-3-70B FP16 GQA = exactly 40.0 GiB
    kv_gib = estimate_kv_cache_gib(batch_size=32, context_tokens=4096)
    assert abs(kv_gib - 40.0) < 1e-6, f"[FAIL Part B] Expected 40.0 GiB, got {kv_gib:.4f}"

    # Verify Part C: Multi-node >8 GPUs must not crash
    try:
        nodes = gpus_required(total_vram_gib=900.0, gpu_vram_gib=80.0)
        assert nodes == 16, f"[FAIL Part C] Expected 16 GPUs, got {nodes}"
    except StopIteration:
        raise AssertionError("[FAIL Part C] gpus_required crashed with StopIteration for >8 GPUs!")

    print("[PASS] Lab V5-01 completed!")
