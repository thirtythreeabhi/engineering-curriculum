"""
Exercise 5.2: LLM Inference Economics and KV Cache Memory Calculator

Problem:
In production LLM serving (e.g. vLLM, TensorRT-LLM), GPU VRAM is consumed by:
1. Model Weights (static VRAM): params * bytes_per_param
   (e.g. 70B FP16 = 140 * 10^9 bytes = 140.0 GB decimal = 130.39 GiB binary).
2. KV Cache (dynamic VRAM per token, matching Vol 5 Ch 9 Eq. 9.2/9.3):
   KV_bytes_per_token = 2 * n_layers * n_kv_heads * head_dim * bytes_per_param
3. Activation memory & CUDA runtime overhead (~20%).

Units note:
All VRAM capacity sizing uses consistent binary GiB (1 GiB = 1024^3 bytes = 1,073,741,824 B)
so model weights, KV cache, and GPU HBM3 capacity (e.g. 80 GiB A100/H100) share the same unit!
For convenience, decimal GB (10^9 bytes, matching Vol 5 Ch 9 Table 9.1) is also reported
for the KV cache so both conventions are explicit and never mixed.
"""

import math
from typing import Dict


GIB = 1024**3
GB = 10**9


class GpuCapacityPlanner:
    def __init__(
        self,
        param_count_billions: float = 70.0,
        n_layers: int = 80,
        n_kv_heads: int = 8,  # Grouped Query Attention (GQA 1:8 on 64 query heads)
        head_dim: int = 128,
        bytes_per_param: int = 2,  # FP16 / BF16
        gpu_vram_gib: float = 80.0,
        gpu_hourly_cost: float = 3.50,
    ):
        self.param_count = param_count_billions * 1e9
        self.n_layers = n_layers
        self.n_kv_heads = n_kv_heads
        self.head_dim = head_dim
        self.bytes_per_param = bytes_per_param
        self.gpu_vram_gib = gpu_vram_gib
        self.gpu_hourly_cost = gpu_hourly_cost

    def calculate_memory_and_cost(
        self,
        batch_size_concurrent_users: int,
        context_length_tokens: int,
    ) -> Dict[str, float]:
        # 1. Static model weight VRAM (bytes -> binary GiB)
        weight_bytes = self.param_count * self.bytes_per_param
        weight_vram_gib = weight_bytes / GIB

        # 2. KV Cache per token: 2 (K + V) * layers * kv_heads * head_dim * bytes_per_param
        kv_bytes_per_token = (
            2 * self.n_layers * self.n_kv_heads * self.head_dim * self.bytes_per_param
        )
        total_kv_bytes = batch_size_concurrent_users * context_length_tokens * kv_bytes_per_token
        kv_vram_gib = total_kv_bytes / GIB
        kv_vram_gb_decimal = total_kv_bytes / GB

        # 3. Overhead buffer (+20% for activations, CUDA graphs, and runtime allocator slack)
        total_vram_gib = (weight_vram_gib + kv_vram_gib) * 1.20

        # 4. GPU sizing: single-node tensor-parallel sizes [1, 2, 4, 8];
        #    for >8 GPUs, scale in 8-GPU multi-node increments (16, 24, 32, ...)
        gpus_needed = max(1, math.ceil(total_vram_gib / self.gpu_vram_gib))
        tp_sizes = [1, 2, 4, 8]
        if gpus_needed <= 8:
            gpus_provisioned = next(tp for tp in tp_sizes if tp >= gpus_needed)
        else:
            gpus_provisioned = 8 * math.ceil(gpus_needed / 8)

        monthly_cost = gpus_provisioned * self.gpu_hourly_cost * 24 * 30

        return {
            "weights_vram_gib": round(weight_vram_gib, 2),
            "kv_cache_vram_gib": round(kv_vram_gib, 2),
            "kv_cache_vram_gb_decimal": round(kv_vram_gb_decimal, 2),
            "total_vram_required_gib": round(total_vram_gib, 2),
            "gpus_needed_raw": gpus_needed,
            "gpus_provisioned": gpus_provisioned,
            "monthly_hosting_cost_usd": round(monthly_cost, 2),
        }


if __name__ == "__main__":
    print("==> Running Exercise 5.2: LLM Inference Economics & KV Cache Math...")
    planner = GpuCapacityPlanner(
        param_count_billions=70.0,
        n_layers=80,
        n_kv_heads=8,
        head_dim=128,
        bytes_per_param=2,  # FP16
    )

    # Check single-stream 4096-token KV cache against Vol 5 Ch 9 (1.34 GB decimal / 1.25 GiB binary)
    single_4k = planner.calculate_memory_and_cost(batch_size_concurrent_users=1, context_length_tokens=4096)
    assert single_4k["kv_cache_vram_gib"] == 1.25
    assert single_4k["kv_cache_vram_gb_decimal"] == 1.34

    # 32 concurrent requests with 4,096 tokens context
    plan = planner.calculate_memory_and_cost(
        batch_size_concurrent_users=32,
        context_length_tokens=4096,
    )
    assert plan["weights_vram_gib"] == 130.39
    assert plan["kv_cache_vram_gib"] == 40.00
    assert plan["total_vram_required_gib"] == 204.46
    assert plan["gpus_provisioned"] == 4
    assert plan["monthly_hosting_cost_usd"] == 10080.00

    # Large multi-node workload (gpus_needed > 8) must scale cleanly without StopIteration
    large_plan = planner.calculate_memory_and_cost(
        batch_size_concurrent_users=64,
        context_length_tokens=32768,
    )
    assert large_plan["gpus_needed_raw"] > 8
    assert large_plan["gpus_provisioned"] >= large_plan["gpus_needed_raw"]
    assert large_plan["gpus_provisioned"] % 8 == 0

    print(
        f"[PASS] Exercise 5.2 verified "
        f"(70B@32x4k -> {plan['gpus_provisioned']}x 80GiB GPUs, ${plan['monthly_hosting_cost_usd']:,.2f}/mo; "
        f"64x32k -> {large_plan['gpus_provisioned']} GPUs)."
    )
