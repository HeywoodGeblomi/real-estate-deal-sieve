#!/usr/bin/env python3
"""
Column mapper + preset profiles for Real-Estate Deal Sieve.

Maps user-friendly profile names to (obj1, higher1, obj2, higher2) pairs
and optional stress re-weighting of the risk axis.

EXTERNAL-clean / no-χ. Structural only.
"""

from __future__ import annotations
from typing import Dict, Tuple, Any

# Preset profiles → (obj1_col, obj1_higher_better, obj2_col, obj2_higher_better)
PROFILES: Dict[str, Tuple[str, bool, str, bool]] = {
    "cashflow": ("cap_rate", True, "risk_score", False),
    "cash_on_cash": ("cash_on_cash", True, "risk_score", False),
    "balanced": ("cap_rate", True, "liquidity_score", True),  # higher liquidity better → invert later
    "appreciation": ("appreciation_potential", True, "risk_score", False),
    "stress_resistant": ("cap_rate", True, "vacancy_risk", False),  # low vacancy preferred
    "liquidity": ("liquidity_score", True, "days_on_market", False),
}

# Stress axes that can be folded into the risk objective later
STRESS_COLUMNS = (
    "vacancy_risk",
    "interest_sensitivity",
    "exit_multiple_proxy",  # higher better, so invert when folding into risk
)

def resolve_profile(name: str) -> Tuple[str, bool, str, bool]:
    key = name.strip().lower().replace("-", "_").replace(" ", "_")
    if key not in PROFILES:
        raise KeyError(f"Unknown profile '{name}'. Available: {list(PROFILES)}")
    return PROFILES[key]


def describe_profiles() -> str:
    lines = ["Available profiles:"]
    for k, (o1, h1, o2, h2) in PROFILES.items():
        d1 = "higher better" if h1 else "lower better"
        d2 = "higher better" if h2 else "lower better"
        lines.append(f"  {k:18s}  obj1={o1} ({d1})  vs  obj2={o2} ({d2})")
    return "\n".join(lines)


if __name__ == "__main__":
    print(describe_profiles())
