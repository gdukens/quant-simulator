"""
Stress testing and scenario analysis.

Provides:
  - Historical stress scenarios (2008 crisis, COVID crash, etc.)
  - Custom hypothetical scenarios
  - Factor shock analysis
  - Sensitivity analysis (single-factor and multi-factor)

All stress tests return a StressTestResult with:
  - Original portfolio value
  - Stressed portfolio value
  - Loss amount and percentage
  - Factor-level breakdown
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd

from quantlib_pro.utils.validation import require_positive

log = logging.getLogger(__name__)


@dataclass
class Scenario:
    """
    A stress scenario defined by factor shocks.

    Attributes
    ----------
    name : str
        Scenario label (e.g., "2008 Financial Crisis", "Oil Shock +50%")
    shocks : dict[str, float]
        Factor → shock magnitude. Example: {"equity": -0.40, "bond": -0.15}
    description : str
        Human-readable description
    historical_date : datetime, optional
        If a historical scenario, the reference date
    """
    name: str
    shocks: dict[str, float]
    description: str = ""
    historical_date: Optional[datetime] = None


@dataclass
class StressTestResult:
    """
    Result of applying a stress scenario to a portfolio.

    Attributes
    ----------
    scenario_name : str
        Name of the applied scenario
    original_value : float
        Portfolio value before stress
    stressed_value : float
        Portfolio value after stress
    loss : float
        Dollar loss (positive = loss)
    loss_pct : float
        Loss as percentage (e.g., 0.15 = 15% loss)
    factor_contributions : dict[str, float]
        Breakdown of loss by factor
    """
    scenario_name: str
    original_value: float
    stressed_value: float
    loss: float
    loss_pct: float
    factor_contributions: dict[str, float] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"Stress Test: {self.scenario_name}\n"
            f"  Original: ${self.original_value:,.2f}\n"
            f"  Stressed: ${self.stressed_value:,.2f}\n"
            f"  Loss: ${self.loss:,.2f} ({self.loss_pct:.2%})"
        )


# ─── Historical scenarios ─────────────────────────────────────────────────────

HISTORICAL_SCENARIOS = {
    "2008_crisis": Scenario(
        name="2008 Financial Crisis",
        shocks={
            "equity": -0.50,
            "corporate_bond": -0.25,
            "real_estate": -0.35,
            "commodities": -0.40,
            "treasury": 0.15,  # flight to quality
        },
        description="Sep-Dec 2008: Lehman collapse, credit freeze",
        historical_date=datetime(2008, 9, 15),
    ),
    "covid_crash": Scenario(
        name="COVID-19 Crash",
        shocks={
            "equity": -0.34,
            "oil": -0.65,
            "corporate_bond": -0.12,
            "treasury": 0.10,
        },
        description="Feb-Mar 2020: Pandemic-induced shutdown",
        historical_date=datetime(2020, 3, 16),
    ),
    "dotcom_bubble": Scenario(
        name="Dot-com Bubble Burst",
        shocks={
            "equity": -0.45,
            "tech": -0.78,
            "bond": 0.05,
        },
        description="Mar 2000 - Oct 2002: Tech valuations collapse",
        historical_date=datetime(2000, 3, 10),
    ),
    "russia_ukraine": Scenario(
        name="Russia-Ukraine War",
        shocks={
            "equity": -0.15,
            "oil": 0.40,
            "natural_gas": 0.80,
            "wheat": 0.50,
            "defense": 0.20,
        },
        description="Feb 2022: Energy and commodity shocks",
        historical_date=datetime(2022, 2, 24),
    ),
    "treasury_shock": Scenario(
        name="Treasury Yield Spike +200bp",
        shocks={
            "treasury_10y": 0.02,  # +200 basis points
            "treasury_30y": 0.025,
            "mortgage": -0.10,
            "equity": -0.08,
        },
        description="Hypothetical: Rapid rate normalization",
    ),
}


# ─── Stress testing engine ────────────────────────────────────────────────────

class StressTestEngine:
    """
    Apply stress scenarios to a portfolio or pricing function.

    Usage::

        engine = StressTestEngine()
        
        # Define portfolio exposures
        exposures = {"equity": 0.60, "bond": 0.30, "real_estate": 0.10}
        
        # Run a historical scenario
        result = engine.run_scenario(
            HISTORICAL_SCENARIOS["2008_crisis"],
            exposures,
            portfolio_value=1_000_000,
        )
        print(result)
    """

    def run_scenario(
        self,
        scenario: Scenario,
        exposures: dict[str, float],
        portfolio_value: float,
    ) -> StressTestResult:
        """
        Apply a stress scenario to a portfolio defined by factor exposures.

        Parameters
        ----------
        scenario : Scenario
            Stress scenario with factor shocks
        exposures : dict[str, float]
            Portfolio weights by factor (should sum to ~1.0)
        portfolio_value : float
            Current portfolio value in dollars

        Returns
        -------
        StressTestResult
            Stressed portfolio value and loss breakdown
        """
        require_positive(portfolio_value, "portfolio_value")

        total_weight = sum(exposures.values())
        if abs(total_weight - 1.0) > 0.01:
            log.warning(
                "Portfolio exposures sum to %.2f, expected ~1.0", total_weight
            )

        factor_contributions = {}
        total_shock = 0.0

        for factor, weight in exposures.items():
            shock = scenario.shocks.get(factor, 0.0)
            contribution = weight * shock
            total_shock += contribution
            factor_contributions[factor] = contribution * portfolio_value

        stressed_value = portfolio_value * (1 + total_shock)
        loss = portfolio_value - stressed_value
        loss_pct = -total_shock

        return StressTestResult(
            scenario_name=scenario.name,
            original_value=portfolio_value,
            stressed_value=stressed_value,
            loss=loss,
            loss_pct=loss_pct,
            factor_contributions=factor_contributions,
        )

    def run_all_historical(
        self,
        exposures: dict[str, float],
        portfolio_value: float,
    ) -> list[StressTestResult]:
        """
        Run all predefined historical scenarios and return sorted by loss.

        Returns
        -------
        list[StressTestResult]
            Results sorted from worst to best
        """
        results = []
        for scenario in HISTORICAL_SCENARIOS.values():
            result = self.run_scenario(scenario, exposures, portfolio_value)
            results.append(result)

        results.sort(key=lambda r: r.loss, reverse=True)
        return results

    def sensitivity_analysis(
        self,
        factor: str,
        shocks: list[float],
        exposures: dict[str, float],
        portfolio_value: float,
    ) -> pd.DataFrame:
        """
        Perform single-factor sensitivity analysis.

        Parameters
        ----------
        factor : str
            Factor to shock (e.g., "equity")
        shocks : list[float]
            List of shock magnitudes (e.g., [-0.30, -0.20, -0.10, 0, 0.10])
        exposures : dict[str, float]
            Portfolio exposures
        portfolio_value : float
            Current portfolio value

        Returns
        -------
        pd.DataFrame
            Columns: shock, stressed_value, loss, loss_pct
        """
        results = []
        for shock in shocks:
            scenario = Scenario(
                name=f"{factor} {shock:+.1%}",
                shocks={factor: shock},
            )
            result = self.run_scenario(scenario, exposures, portfolio_value)
            results.append({
                "shock": shock,
                "stressed_value": result.stressed_value,
                "loss": result.loss,
                "loss_pct": result.loss_pct,
            })

        return pd.DataFrame(results)

    def tail_risk_scenarios(
        self,
        exposures: dict[str, float],
        portfolio_value: float,
        n_scenarios: int = 100,
        random_seed: Optional[int] = None,
    ) -> list[StressTestResult]:
        """
        Generate random tail-risk scenarios using extreme shocks.

        Each scenario draws factor shocks from a fat-tailed distribution
        (Student's t with df=3) to simulate extreme market moves.

        Returns
        -------
        list[StressTestResult]
            Random stress scenarios sorted by loss
        """
        rng = np.random.default_rng(random_seed)
        results = []

        factors = list(exposures.keys())
        for i in range(n_scenarios):
            # Draw from t(df=3) scaled to ±30% typical shock
            raw_shocks = rng.standard_t(df=3, size=len(factors)) * 0.10
            shocks = {factor: float(shock) for factor, shock in zip(factors, raw_shocks)}
            
            scenario = Scenario(
                name=f"Random Tail Scenario #{i+1}",
                shocks=shocks,
                description="Randomly generated extreme shock",
            )
            result = self.run_scenario(scenario, exposures, portfolio_value)
            results.append(result)

        results.sort(key=lambda r: r.loss, reverse=True)
        return results


# ─── Convenience functions ────────────────────────────────────────────────────

def run_stress_test(
    scenario_name: str,
    exposures: dict[str, float],
    portfolio_value: float,
) -> StressTestResult:
    """
    Run a predefined historical stress scenario.

    Parameters
    ----------
    scenario_name : str
        One of: "2008_crisis", "covid_crash", "dotcom_bubble",
        "russia_ukraine", "treasury_shock"

    Returns
    -------
    StressTestResult
    """
    if scenario_name not in HISTORICAL_SCENARIOS:
        raise ValueError(
            f"Unknown scenario '{scenario_name}'. "
            f"Available: {list(HISTORICAL_SCENARIOS.keys())}"
        )

    engine = StressTestEngine()
    scenario = HISTORICAL_SCENARIOS[scenario_name]
    return engine.run_scenario(scenario, exposures, portfolio_value)
