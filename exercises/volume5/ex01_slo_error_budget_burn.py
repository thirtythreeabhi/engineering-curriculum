"""
Exercise 5.1: SRE SLO Error Budget and Multi-Window Burn Rate Calculator

Problem:
Site Reliability Engineering (SRE) manages reliability through Service Level Objectives (SLOs)
and Error Budgets.
Given:
- Rolling window: 30 days = 43,200 minutes.
- SLO: 99.9% availability (Three Nines).
- Error Budget = 100% - 99.9% = 0.1% = 43.2 minutes of total downtime.

Implement a BurnRateCalculator:
1. Computes total allowed error budget for any SLO percentage.
2. Calculates current consumed error budget and remaining balance.
3. Evaluates multi-window burn rates (e.g., 14.4x burn consumes 2% of budget in 1 hour).
"""

from typing import Dict


class SreErrorBudgetCalculator:
    def __init__(self, target_slo: float = 0.999, window_days: int = 30):
        self.target_slo = target_slo
        self.window_minutes = window_days * 24 * 60
        self.total_budget_minutes = self.window_minutes * (1.0 - target_slo)

    def evaluate_consumption(self, downtime_minutes_spent: float) -> Dict[str, float]:
        remaining = max(0.0, self.total_budget_minutes - downtime_minutes_spent)
        pct_consumed = (downtime_minutes_spent / self.total_budget_minutes) * 100.0
        return {
            "total_budget_minutes": round(self.total_budget_minutes, 2),
            "consumed_minutes": round(downtime_minutes_spent, 2),
            "remaining_minutes": round(remaining, 2),
            "percent_consumed": round(pct_consumed, 2),
        }

    def compute_burn_rate(self, window_hours: float, budget_fraction_consumed: float) -> float:
        """
        Burn rate = (fraction_consumed) / (window_hours / total_window_hours)
        A burn rate of 1.0 consumes exactly 100% of budget over 30 days.
        A burn rate of 14.4 consumes 2% of budget in 1 hour (Google SRE Alerting standard).
        """
        total_hours = self.window_minutes / 60.0
        time_fraction = window_hours / total_hours
        return round(budget_fraction_consumed / time_fraction, 2)


if __name__ == "__main__":
    print("==> Running Exercise 5.1: SRE Error Budget & Burn Rate Calculator...")
    calc = SreErrorBudgetCalculator(target_slo=0.999, window_days=30)

    # 30 days = 43,200 mins. 0.1% budget = 43.2 minutes
    assert abs(calc.total_budget_minutes - 43.2) < 0.01

    status = calc.evaluate_consumption(10.8) # 1/4 consumed
    assert status["remaining_minutes"] == 32.4
    assert status["percent_consumed"] == 25.0

    # Google SRE: 2% budget consumed in 1 hour -> 14.4x burn rate
    burn = calc.compute_burn_rate(window_hours=1.0, budget_fraction_consumed=0.02)
    assert burn == 14.4

    print(f"[PASS] Exercise 5.1 verified (Budget: {calc.total_budget_minutes} mins, 1h 2% Burn Rate = {burn}x).")
