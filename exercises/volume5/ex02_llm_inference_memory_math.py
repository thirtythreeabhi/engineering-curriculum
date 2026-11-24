"""
Exercise 5.2: LLM Inference Economics and KV Cache Memory Calculator

Problem:
In production LLM serving (e.g. vLLM, TensorRT-LLM), memory is consumed by:
1. Model Weights (static VRAM): params * bytes_per_param (e.g. 70B FP16 = 140 GB).
2. KV Cache (dynamic VRAM per token):
   KV_bytes_per_token = 2 * n_layers * n_kv_heads * head_dim * bytes_per_param
3. Activation memory & runtime buffer (~20%).

Implement a GPUCapacityPlanner:
- Calculates static and dynamic VRAM requirements.
- Determines number of 80GB GPUs (A100/H100) needed for target concurrent users.
- Calculates monthly infrastructure hosting cost.
"""

from typing import Dict


class GpuCapacityPlanner:
    def __init__(
        self,
        param_count_billions: float = 70.0,
        n_layers: int = 80,
        n_kv_heads: int = 8,  # Grouped Query Attention (GQA)
        head_dim: int = 128,
        bytes_per_param: int = 2,  # FP16 / BF16
        gpu_vram_gb: float = 80.0,
        gpu_hourly_cost: float = 3.50,
    ):
        self.param_count = param_count_billions * 1e9
        self.n_layers = n_layers
        self.n_kv_heads = n_kv_heads
        self.head_dim = head_dim
        self.bytes_per_param = bytes_per_param
        self.gpu_vram_gb = gpu_vram_gb
        self.gpu_hourly_cost = gpu_hourly_cost

    def calculate_memory_and_cost(
        self,
        batch_size_concurrent_users: int,
        context_length_tokens: int,
    ) -> Dict[str, float]:
        # 1. Static model weight VRAM (in GB)
        weight_vram_gb = (self.param_count * self.bytes_per_param) / (1024**3)

        # 2. KV Cache per token: 2 (keys + values) * layers * kv_heads * head_dim * bytes
        kv_bytes_per_token = 2 * self.n_layers * self.n_kv_heads * self.head_dim * self.bytes_per_param
        total_kv_bytes = batch_size_concurrent_users * context_length_tokens * kv_bytes_per_token
        kv_vram_gb = total_kv_bytes / (1024**3)

        # 3. Overhead buffer (20% for activations and CUDA runtime)
        total_vram_gb = (weight_vram_gb + kv_vram_gb) * 1.20

        # 4. GPU sizing
        gpus_needed = max(1, int(-(-total_vram_gb // self.gpu_vram_gb)))  # Ceiling division
        # Common tensor-parallel sizes: 1, 2, 4, 8
        tp_sizes = [1, 2, 4, 8]
        gpus_provisioned = next(tp for tp in tp_sizes if tp >= gpus_needed)

        monthly_cost = gpus_provisioned * self.gpu_hourly_cost * 24 * 30

        return {
            "weights_vram_gb": round(weight_vram_gb, 2),
            "kv_cache_vram_gb": round(kv_vram_gb, 2),
            "total_vram_required_gb": round(total_vram_gb, 2),
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
        bytes_per_param=2, # FP16
    )

    # 32 concurrent requests with 4,096 tokens context
    plan = planner.calculate_memory_and_cost(
        batch_size_concurrent_users=32,
        context_length_tokens=4096,
    )

    # 70B FP16 weights = ~130.38 GB
    assert plan["weights_vram_gb"] > 130.0
    # KV cache for 32 * 4096 tokens with GQA = ~20 GB
    assert plan["kv_cache_vram_gb"] > 18.0
    # Requires 4 x 80GB GPUs
    assert plan["gpus_provisioned"] == 4
    # Monthly cost: 4 GPUs * $3.50 * 720h = $10,080.00
    assert plan["monthly_hosting_cost_usd"] == 10080.00

    print(f"[PASS] Exercise 5.2 verified (70B model requires {plan['gpus_provisioned']}x 80GB GPUs, monthly cost: ${plan['monthly_hosting_cost_usd']:,.2f}).")
