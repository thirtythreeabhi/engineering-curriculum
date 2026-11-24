"""
Exercise 5.4: Cloud FinOps Compute Cost Rightsizer and Commitment Optimizer

Problem:
FinOps (Cloud Financial Operations) optimizes cloud unit economics by matching workload
variability with appropriate pricing models:
1. On-Demand: 100% price, zero commitment (for bursty / unpredictable workloads).
2. 1-Year Reserved Instance (RI): ~40% discount with 1-year commitment.
3. 3-Year Savings Plan: ~65% discount with 3-year commitment.

Implement a FinOpsCommitmentOptimizer:
- Calculates annual spend across pricing models.
- Determines the Breakeven Utilization threshold: how many hours per month an instance
  must run before an RI or Savings Plan becomes cheaper than On-Demand.
"""

from typing import Dict


class FinOpsCommitmentOptimizer:
    def __init__(
        self,
        on_demand_hourly: float = 1.00,
        ri_1yr_effective_hourly: float = 0.60,
        savings_plan_3yr_effective_hourly: float = 0.35,
    ):
        self.on_demand = on_demand_hourly
        self.ri_1yr = ri_1yr_effective_hourly
        self.sp_3yr = savings_plan_3yr_effective_hourly

    def calculate_annual_spend(self, instance_count: int, utilization_pct: float = 1.0) -> Dict[str, float]:
        total_hours = 8760.0  # 365 * 24
        active_hours = total_hours * utilization_pct

        # On-Demand only pays for active hours
        on_demand_spend = instance_count * active_hours * self.on_demand

        # Commitments pay for all committed hours (8,760 hours/yr)
        ri_1yr_spend = instance_count * total_hours * self.ri_1yr
        sp_3yr_spend = instance_count * total_hours * self.sp_3yr

        return {
            "on_demand_annual": round(on_demand_spend, 2),
            "ri_1yr_annual": round(ri_1yr_spend, 2),
            "sp_3yr_annual": round(sp_3yr_spend, 2),
            "ri_savings_pct": round(((on_demand_spend - ri_1yr_spend) / on_demand_spend) * 100.0, 2) if on_demand_spend > ri_1yr_spend else 0.0,
            "sp_savings_pct": round(((on_demand_spend - sp_3yr_spend) / on_demand_spend) * 100.0, 2) if on_demand_spend > sp_3yr_spend else 0.0,
        }

    def compute_breakeven_utilization(self) -> Dict[str, float]:
        """
        Breakeven utilization = committed_hourly / on_demand_hourly
        If workload runs more than this fraction of the month, commitment saves money!
        """
        ri_breakeven = (self.ri_1yr / self.on_demand) * 100.0
        sp_breakeven = (self.sp_3yr / self.on_demand) * 100.0
        return {
            "ri_1yr_breakeven_pct": round(ri_breakeven, 2),
            "sp_3yr_breakeven_pct": round(sp_breakeven, 2),
        }


if __name__ == "__main__":
    print("==> Running Exercise 5.4: Cloud FinOps Commitment Optimizer...")
    optimizer = FinOpsCommitmentOptimizer(
        on_demand_hourly=1.20,
        ri_1yr_effective_hourly=0.72, # 40% discount
        savings_plan_3yr_effective_hourly=0.42, # 65% discount
    )

    # 10 instances running 24/7 (100% utilization)
    full_spend = optimizer.calculate_annual_spend(instance_count=10, utilization_pct=1.0)
    assert full_spend["on_demand_annual"] == 105120.00
    assert full_spend["ri_1yr_annual"] == 63072.00
    assert full_spend["sp_3yr_annual"] == 36792.00
    assert full_spend["ri_savings_pct"] == 40.0
    assert full_spend["sp_savings_pct"] == 65.0

    # Breakeven thresholds
    be = optimizer.compute_breakeven_utilization()
    assert be["ri_1yr_breakeven_pct"] == 60.0
    assert be["sp_3yr_breakeven_pct"] == 35.0

    print(f"[PASS] Exercise 5.4 verified (3-Year Savings Plan saves ${full_spend['on_demand_annual'] - full_spend['sp_3yr_annual']:,.2f} / yr on 10 instances).")
