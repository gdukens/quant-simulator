"""Suite B: Risk Analysis & Metrics

Consolidates:
- Real-Time-Stress-Detection (market risk variant)
- Tail-Risk-Distribution-Morph-Engine
- Portfolio-Fragility-Hidden-Leverage-Map
"""

# Risk limits (Week 2)
from quantlib_pro.risk.limits import (
    LimitBreach,
    LimitCheckResult,
    LimitStatus,
    PortfolioLimit,
    PositionLimit,
    RiskLimitFramework,
    limits,
)

# VaR and CVaR (Week 4)
from quantlib_pro.risk.var import (
    VaRMethod,
    VaRResult,
    calculate_var,
    var_cornish_fisher,
    var_historical,
    var_monte_carlo,
    var_parametric,
)

# Stress testing (Week 4)
from quantlib_pro.risk.stress_testing import (
    Scenario,
    StressTestEngine,
    StressTestResult,
    run_stress_test,
)

__all__ = [
    # Limits
    "RiskLimitFramework",
    "LimitCheckResult",
    "LimitBreach",
    "LimitStatus",
    "PositionLimit",
    "PortfolioLimit",
    "limits",
    # VaR
    "VaRMethod",
    "VaRResult",
    "calculate_var",
    "var_historical",
    "var_parametric",
    "var_monte_carlo",
    "var_cornish_fisher",
    # Stress Testing
    "Scenario",
    "StressTestEngine",
    "StressTestResult",
    "run_stress_test",
]
