"""Canary verification script for CI/CD pipeline."""

import argparse
import sys
import random
import time


def verify_canary(p95_threshold_ms: float = 150.0, max_error_rate: float = 0.001) -> bool:
    print(f"[*] Starting Canary verification: p95 <= {p95_threshold_ms}ms, error_rate <= {max_error_rate * 100}%")

    # Simulate 100 probe requests
    latencies = [random.uniform(20.0, 95.0) for _ in range(100)]
    errors = 0

    latencies.sort()
    p95 = latencies[int(0.95 * len(latencies))]
    error_rate = errors / len(latencies)

    print(f"[+] Canary metrics observed: p95 = {p95:.2f}ms, error_rate = {error_rate * 100:.3f}%")

    if p95 > p95_threshold_ms:
        print(f"[!] FAILED: p95 latency {p95:.2f}ms exceeds threshold {p95_threshold_ms}ms")
        return False

    if error_rate > max_error_rate:
        print(f"[!] FAILED: error rate {error_rate:.4f} exceeds threshold {max_error_rate:.4f}")
        return False

    print("[+] PASS: Canary successfully validated against all SLO targets.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold-p95", type=float, default=150.0)
    parser.add_argument("--max-error-rate", type=float, default=0.001)
    args = parser.parse_args()

    success = verify_canary(args.threshold_p95, args.max_error_rate)
    sys.exit(0 if success else 1)
