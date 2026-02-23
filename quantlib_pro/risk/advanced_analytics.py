"""
Advanced Risk Analytics and Stress Testing Engine.

Comprehensive risk analysis tools:
- Scenario analysis (historical and hypothetical)
- Monte Carlo stress testing
- Correlation breakdown analysis
- Tail risk analysis  
- Risk factor attribution
- Extreme value theory (EVT)

Example
-------
>>> from quantlib_pro.risk.advanced_analytics import StressTester, ScenarioAnalyzer
>>>
>>> # Stress testing
>>> stress_tester = StressTester(portfolio_returns)
>>> results = stress_tester.run_monte_carlo_stress(n_scenarios=10000)
>>> print(results.summary())
>>>
>>> # Scenario analysis
>>> analyzer = ScenarioAnalyzer(portfolio)
>>> scenarios = analyzer.generate_historical_scenarios(['2008 Crisis', '2020 COVID'])
>>> impact = analyzer.analyze_scenario(scenarios['2008 Crisis'])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

log = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of stress scenarios."""
    HISTORICAL = 'historical'
    HYPOTHETICAL = 'hypothetical'
    MONTE_CARLO = 'monte_carlo'
    REGULATORY = 'regulatory'


@dataclass
class Scenario:
    """Stress test scenario definition."""
    name: str
    scenario_type: ScenarioType
    description: str
    market_shocks: Dict[str, float]  # asset -> return shock
    correlation_multiplier: float = 1.0  # Correlation intensification factor
    volatility_multiplier: float = 1.0  # Volatility scaling factor
    
    def apply_shock(self, returns: pd.Series) -> pd.Series:
        """Apply scenario shocks to returns."""
        shocked_returns = returns.copy()
        
        for asset, shock in self.market_shocks.items():
            if asset in shocked_returns.index:
                shocked_returns[asset] = shock
        
        return shocked_returns


@dataclass
class StressTestResult:
    """Results from stress testing."""
    scenario_name: str
    portfolio_loss: float
    portfolio_loss_pct: float
    var_95: float
    cvar_95: float
    max_drawdown: float
    sharpe_ratio: float
    asset_contributions: Dict[str, float]
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    
    def summary(self) -> str:
        """Generate summary string."""
        return f"""
Stress Test Results: {self.scenario_name}
{'=' * 60}
Portfolio Loss:       ${self.portfolio_loss:,.2f} ({self.portfolio_loss_pct:.2%})
VaR (95%):           {self.var_95:.2%}
CVaR (95%):          {self.cvar_95:.2%}
Max Drawdown:        {self.max_drawdown:.2%}
Sharpe Ratio:        {self.sharpe_ratio:.2f}

Top Asset Contributions:
{self._format_contributions()}
"""
    
    def _format_contributions(self) -> str:
        """Format asset contributions."""
        sorted_contribs = sorted(
            self.asset_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:10]
        
        lines = []
        for asset, contrib in sorted_contribs:
            lines.append(f"  {asset:>10}: {contrib:>10.2%}")
        
        return '\n'.join(lines)


class StressTester:
    """
    Comprehensive stress testing engine.
    
    Performs various stress tests including historical scenarios,
    hypothetical shocks, and Monte Carlo simulations.
    
    Parameters
    ----------
    returns : pd.DataFrame
        Historical returns data (assets × time)
    weights : np.ndarray, optional
        Portfolio weights
    """
    
    def __init__(
        self,
        returns: pd.DataFrame,
        weights: Optional[np.ndarray] = None,
    ):
        self.returns = returns
        self.weights = weights if weights is not None else np.ones(len(returns.columns)) / len(returns.columns)
        
        # Calculate base statistics
        self.mean_returns = returns.mean()
        self.cov_matrix = returns.cov()
        self.std_returns = returns.std()
        self.correlation = returns.corr()
        
        log.info(f"Initialized StressTester with {len(returns.columns)} assets, {len(returns)} periods")
    
    def run_monte_carlo_stress(
        self,
        n_scenarios: int = 10000,
        stress_level: float = 2.0,
        correlation_breakdown: bool = True,
    ) -> StressTestResult:
        """
        Run Monte Carlo stress test.
        
        Parameters
        ----------
        n_scenarios : int
            Number of scenarios to simulate
        stress_level : float
            Stress intensity (standard deviations)
        correlation_breakdown : bool
            Whether to simulate correlation breakdown
        
        Returns
        -------
        StressTestResult
            Stress test results
        """
        log.info(f"Running Monte Carlo stress test: {n_scenarios} scenarios, stress={stress_level}σ")
        
        # Generate stressed scenarios
        if correlation_breakdown:
            # Reduce correlations during stress
            stressed_corr = self.correlation * 0.5
            stressed_cov = self._correlation_to_covariance(stressed_corr, self.std_returns)
        else:
            stressed_cov = self.cov_matrix
        
        # Generate scenarios
        scenarios = np.random.multivariate_normal(
            mean=-self.mean_returns * stress_level,  # Negative shock
            cov=stressed_cov * (stress_level ** 2),
            size=n_scenarios
        )
        
        # Calculate portfolio returns for each scenario
        portfolio_returns = scenarios @ self.weights
        
        # Calculate metrics
        portfolio_loss = np.min(portfolio_returns)
        portfolio_loss_pct = portfolio_loss
        
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        # Max drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Sharpe ratio
        sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252) if portfolio_returns.std() > 0 else 0
        
        # Asset contributions (average contribution to portfolio variance)
        asset_contributions = self._calculate_risk_contributions(scenarios)
        
        return StressTestResult(
            scenario_name=f"Monte Carlo Stress ({stress_level}σ, N={n_scenarios})",
            portfolio_loss=portfolio_loss,
            portfolio_loss_pct=portfolio_loss_pct,
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            asset_contributions=asset_contributions,
        )
    
    def run_historical_scenario(
        self,
        scenario_name: str,
        start_date: str,
        end_date: str,
    ) -> StressTestResult:
        """
        Run historical scenario analysis.
        
        Parameters
        ----------
        scenario_name : str
            Name of historical scenario
        start_date : str
            Scenario start date
        end_date : str
            Scenario end date
        
        Returns
        -------
        StressTestResult
            Stress test results
        """
        log.info(f"Running historical scenario: {scenario_name} ({start_date} to {end_date})")
        
        # Filter historical returns for scenario period
        scenario_returns = self.returns.loc[start_date:end_date]
        
        if scenario_returns.empty:
            log.warning(f"No data found for scenario period")
            # Return empty result
            return self._empty_result(scenario_name)
        
        # Calculate portfolio returns
        portfolio_returns = (scenario_returns @ self.weights).values
        
        # Calculate metrics
        portfolio_loss = np.min(portfolio_returns)
        portfolio_loss_pct = portfolio_loss
        
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        # Max drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Sharpe ratio
        sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252) if portfolio_returns.std() > 0 else 0
        
        # Asset contributions
        asset_contributions = self._calculate_risk_contributions(scenario_returns.values)
        
        return StressTestResult(
            scenario_name=f"Historical: {scenario_name}",
            portfolio_loss=portfolio_loss,
            portfolio_loss_pct=portfolio_loss_pct,
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            asset_contributions=asset_contributions,
        )
    
    def run_hypothetical_scenario(self, scenario: Scenario) -> StressTestResult:
        """
        Run hypothetical scenario.
        
        Parameters
        ----------
        scenario : Scenario
            Scenario definition
        
        Returns
        -------
        StressTestResult
            Stress test results
        """
        log.info(f"Running hypothetical scenario: {scenario.name}")
        
        # Apply shocks to mean returns
        shocked_returns = self.mean_returns.copy()
        for asset, shock in scenario.market_shocks.items():
            if asset in shocked_returns.index:
                shocked_returns[asset] = shock
        
        # Apply correlation and volatility multipliers
        stressed_cov = self.cov_matrix * (scenario.volatility_multiplier ** 2)
        
        if scenario.correlation_multiplier != 1.0:
            stressed_corr = self.correlation * scenario.correlation_multiplier
            # Clip to valid correlation range
            stressed_corr = np.clip(stressed_corr, -1, 1)
            stressed_cov = self._correlation_to_covariance(stressed_corr, self.std_returns * scenario.volatility_multiplier)
        
        # Simulate scenarios
        n_scenarios = 1000
        scenarios = np.random.multivariate_normal(
            mean=shocked_returns.values,
            cov=stressed_cov.values,
            size=n_scenarios
        )
        
        # Calculate portfolio returns
        portfolio_returns = scenarios @ self.weights
        
        # Calculate metrics
        portfolio_loss = np.min(portfolio_returns)
        portfolio_loss_pct = portfolio_loss
        
        var_95 = np.percentile(portfolio_returns, 5)
        cvar_95 = portfolio_returns[portfolio_returns <= var_95].mean()
        
        # Max drawdown
        cumulative = (1 + portfolio_returns).cumprod()
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Sharpe ratio
        sharpe = portfolio_returns.mean() / portfolio_returns.std() * np.sqrt(252) if portfolio_returns.std() > 0 else 0
        
        # Asset contributions
        asset_contributions = self._calculate_risk_contributions(scenarios)
        
        return StressTestResult(
            scenario_name=f"Hypothetical: {scenario.name}",
            portfolio_loss=portfolio_loss,
            portfolio_loss_pct=portfolio_loss_pct,
            var_95=var_95,
            cvar_95=cvar_95,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            asset_contributions=asset_contributions,
        )
    
    def _calculate_risk_contributions(self, scenarios: np.ndarray) -> Dict[str, float]:
        """Calculate risk contributions for each asset."""
        contributions = {}
        
        # Calculate marginal contribution to risk
        portfolio_var = np.var(scenarios @ self.weights)
        
        for i, asset in enumerate(self.returns.columns):
            # Contribution = weight × (covariance with portfolio / portfolio variance)
            asset_returns = scenarios[:, i]
            portfolio_returns = scenarios @ self.weights
            
            cov = np.cov(asset_returns, portfolio_returns)[0, 1]
            contribution = self.weights[i] * cov / portfolio_var if portfolio_var > 0 else 0
            
            contributions[asset] = contribution
        
        return contributions
    
    def _correlation_to_covariance(
        self,
        correlation: pd.DataFrame,
        std: pd.Series,
    ) -> pd.DataFrame:
        """Convert correlation matrix to covariance matrix."""
        std_matrix = np.outer(std.values, std.values)
        cov = correlation.values * std_matrix
        return pd.DataFrame(cov, index=correlation.index, columns=correlation.columns)
    
    def _empty_result(self, name: str) -> StressTestResult:
        """Create empty result."""
        return StressTestResult(
            scenario_name=name,
            portfolio_loss=0.0,
            portfolio_loss_pct=0.0,
            var_95=0.0,
            cvar_95=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            asset_contributions={},
        )


class TailRiskAnalyzer:
    """
    Extreme value theory (EVT) tail risk analysis.
    
    Analyzes tail risk using:
    - Peaks Over Threshold (POT) method
    - Generalized Pareto Distribution (GPD)
    - Hill estimator for tail index
    """
    
    def __init__(self, returns: pd.Series):
        self.returns = returns
        self.negative_returns = -returns[returns < 0]
        
        log.info("Initialized TailRiskAnalyzer")
    
    def estimate_tail_index(self, threshold_percentile: float = 0.90) -> float:
        """
        Estimate tail index using Hill estimator.
        
        Parameters
        ----------
        threshold_percentile : float
            Percentile threshold for tail (e.g., 0.90 = top 10%)
        
        Returns
        -------
        float
            Tail index estimate
        """
        threshold = self.negative_returns.quantile(threshold_percentile)
        exceedances = self.negative_returns[self.negative_returns > threshold]
        
        if len(exceedances) == 0:
            return 0.0
        
        # Hill estimator
        log_exceedances = np.log(exceedances / threshold)
        tail_index = 1 / log_exceedances.mean()
        
        return tail_index
    
    def fit_gpd(self, threshold_percentile: float = 0.90) -> Tuple[float, float]:
        """
        Fit Generalized Pareto Distribution to tail.
        
        Parameters
        ----------
        threshold_percentile : float
            Percentile threshold
        
        Returns
        -------
        tuple of (shape, scale)
            GPD parameters
        """
        threshold = self.negative_returns.quantile(threshold_percentile)
        exceedances = self.negative_returns[self.negative_returns > threshold] - threshold
        
        if len(exceedances) < 10:
            return (0.0, 0.0)
        
        # Fit GPD using scipy
        shape, loc, scale = stats.genpareto.fit(exceedances, floc=0)
        
        return (shape, scale)
    
    def calculate_extreme_var(
        self,
        confidence: float = 0.99,
        threshold_percentile: float = 0.90,
    ) -> float:
        """
        Calculate VaR using EVT.
        
        Parameters
        ----------
        confidence : float
            Confidence level for VaR
        threshold_percentile : float
            Threshold for tail definition
        
        Returns
        -------
        float
            Extreme VaR estimate
        """
        threshold = self.negative_returns.quantile(threshold_percentile)
        shape, scale = self.fit_gpd(threshold_percentile)
        
        if scale == 0:
            # Fallback to empirical quantile
            return self.negative_returns.quantile(confidence)
        
        # Calculate extreme VaR using GPD
        n = len(self.negative_returns)
        n_exceedances = len(self.negative_returns[self.negative_returns > threshold])
        
        q = (n / n_exceedances) * (1 - confidence)
        
        if shape != 0:
            extreme_var = threshold + (scale / shape) * (q ** (-shape) - 1)
        else:
            extreme_var = threshold - scale * np.log(q)
        
        return extreme_var
