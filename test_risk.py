#!/usr/bin/env python
"""Quick smoke test for Week 4 risk module."""
import numpy as np
from quantlib_pro.risk import (
    var_historical, var_parametric, var_monte_carlo, calculate_var, VaRMethod,
    Scenario, StressTestEngine,
)

np.random.seed(42)
returns = np.random.normal(0.0005, 0.015, 252)
pv = 1_000_000

# VaR
var = var_historical(returns, confidence_level=0.95)
var.portfolio_value = pv
print(f"Historical VaR (95%): {var.var:.4f} = ${var.var_dollars:,.0f}")

var_p = var_parametric(returns, confidence_level=0.95)
var_p.portfolio_value = pv
print(f"Parametric VaR (95%): {var_p.var:.4f} = ${var_p.var_dollars:,.0f}")

var_mc = var_monte_carlo(returns, confidence_level=0.95, n_simulations=5_000, random_seed=42)
var_mc.portfolio_value = pv
print(f"Monte Carlo VaR (95%): {var_mc.var:.4f} = ${var_mc.var_dollars:,.0f}")

# Stress Testing
s1 = Scenario("2008_Crisis", {"equity": -0.40}, "Financial crisis")
s2 = Scenario("COVID", {"equity": -0.30}, "Pandemic")
engine = StressTestEngine()
engine.add_scenario(s1)
engine.add_scenario(s2)

def valuator(shocks):
    return pv * (1 + shocks.get("equity", 0))

results = engine.run_all(valuator)
for r in results:
    loss = pv - r.stressed_value
    print(f"Stress {r.scenario_name}: Value=${r.stressed_value:,.0f}, Loss=${loss:,.0f}")

print("\nAll Week 4 risk module tests passed ✓")
