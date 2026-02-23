"""
Value at Risk (VaR) and Conditional Value at Risk (CVaR) calculators.

Methods implemented:
  - Historical simulation
  - Parametric (variance-covariance)
  - Monte Carlo simulation
  - Cornish-Fisher expansion (semi-parametric)

All methods return both VaR and CVaR (also known as Expected Shortfall).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import norm, t as t_dist

from quantlib_pro.utils.validation import require_positive, require_probability

log = logging.getLogger(__name__)


class VaRMethod(str, Enum):
    HISTORICAL = "historical"
    PARAMETRIC = "parametric"
    MONTE_CARLO = "monte_carlo"
    CORNISH_FISHER = "cornish_fisher"


@dataclass
class VaRResult:
    """
    VaR and CVaR results for a single confidence level.

    Attributes
    ----------
    var : float
        Value at Risk — the maximum expected loss at the given confidence level
        (positive number represents loss)
    cvar : float
        Conditional VaR (Expected Shortfall) — average loss beyond VaR
    confidence_level : float
        Confidence level (e.g., 0.95 for 95%)
    method : VaRMethod
        Calculation method used
    time_horizon : float
        Time horizon in days
    portfolio_value : float
        Current portfolio value (optional, for dollar VaR)
    """
    var: float
    cvar: float
    confidence_level: float
    method: VaRMethod
    time_horizon: float = 1.0
    portfolio_value: Optional[float] = None

    @property
    def var_dollars(self) -> Optional[float]:
        """VaR in dollars (if portfolio_value is set)."""
        if self.portfolio_value is None:
            return None
        return self.var * self.portfolio_value

    @property
    def cvar_dollars(self) -> Optional[float]:
        """CVaR in dollars (if portfolio_value is set)."""
        if self.portfolio_value is None:
            return None
        return self.cvar * self.portfolio_value


# ─── Historical VaR ───────────────────────────────────────────────────────────

def var_historical(
    returns: pd.Series | np.ndarray,
    confidence_level: float = 0.95,
    time_horizon: int = 1,
) -> VaRResult:
    """
    Historical simulation VaR/CVaR.

    Parameters
    ----------
    returns : array-like
        Historical returns series (daily, assumed i.i.d.)
    confidence_level : float
        Confidence level (e.g., 0.95 for 95%)
    time_horizon : int
        Number of days to scale VaR (√t scaling)

    Returns
    -------
    VaRResult
        VaR and CVaR as fractions of portfolio value
    """
    require_probability(confidence_level, "confidence_level")
    require_positive(time_horizon, "time_horizon")

    if isinstance(returns, pd.Series):
        returns = returns.values
    returns = returns[~np.isnan(returns)]

    if len(returns) < 30:
        log.warning("Historical VaR with <30 observations may be unreliable")

    # Scale returns by √t if horizon > 1
    if time_horizon > 1:
        scaled_returns = returns * math.sqrt(time_horizon)
    else:
        scaled_returns = returns

    # VaR is the (1 - confidence_level) percentile of the loss distribution
    # Loss = -return, so VaR = -percentile(returns, alpha)
    alpha = 1 - confidence_level
    var = -np.percentile(scaled_returns, alpha * 100)

    # CVaR is the average of all losses beyond VaR
    tail_losses = -scaled_returns[scaled_returns < -var]
    if len(tail_losses) > 0:
        cvar = tail_losses.mean()
    else:
        cvar = var  # fallback if no tail observations

    return VaRResult(
        var=var,
        cvar=cvar,
        confidence_level=confidence_level,
        method=VaRMethod.HISTORICAL,
        time_horizon=time_horizon,
    )


# ─── Parametric VaR ───────────────────────────────────────────────────────────

def var_parametric(
    returns: pd.Series | np.ndarray,
    confidence_level: float = 0.95,
    time_horizon: int = 1,
    distribution: str = "normal",
) -> VaRResult:
    """
    Parametric (variance-covariance) VaR/CVaR.

    Assumes returns are normally or t-distributed.

    Parameters
    ----------
    distribution : str
        "normal" or "t" (Student's t with df estimated from data)
    """
    require_probability(confidence_level, "confidence_level")
    require_positive(time_horizon, "time_horizon")

    if isinstance(returns, pd.Series):
        returns = returns.values
    returns = returns[~np.isnan(returns)]

    mu = returns.mean()
    sigma = returns.std(ddof=1)

    # Scale for time horizon
    mu_scaled = mu * time_horizon
    sigma_scaled = sigma * math.sqrt(time_horizon)

    alpha = 1 - confidence_level

    if distribution == "normal":
        z = norm.ppf(alpha)
        var = -(mu_scaled + z * sigma_scaled)
        # CVaR for normal: VaR + σ * φ(z) / α
        cvar = var + sigma_scaled * norm.pdf(z) / alpha

    elif distribution == "t":
        # Estimate degrees of freedom via method of moments (kurtosis)
        kurtosis = pd.Series(returns).kurtosis()
        df = max(4, 6 / kurtosis + 4) if kurtosis > 0 else 10
        t_val = t_dist.ppf(alpha, df=df)
        var = -(mu_scaled + t_val * sigma_scaled)
        # CVaR for t-distribution (approximation)
        cvar = var * (df + t_val**2) / ((df - 1) * (1 - alpha))
    else:
        raise ValueError(f"Unknown distribution: {distribution}")

    return VaRResult(
        var=var,
        cvar=cvar,
        confidence_level=confidence_level,
        method=VaRMethod.PARAMETRIC,
        time_horizon=time_horizon,
    )


# ─── Monte Carlo VaR ──────────────────────────────────────────────────────────

def var_monte_carlo(
    returns: pd.Series | np.ndarray,
    confidence_level: float = 0.95,
    time_horizon: int = 1,
    n_simulations: int = 10_000,
    random_seed: Optional[int] = None,
) -> VaRResult:
    """
    Monte Carlo VaR/CVaR via bootstrapping historical returns.

    Parameters
    ----------
    n_simulations : int
        Number of bootstrap samples
    random_seed : int, optional
        Random seed for reproducibility
    """
    require_probability(confidence_level, "confidence_level")
    require_positive(time_horizon, "time_horizon")
    require_positive(n_simulations, "n_simulations")

    if isinstance(returns, pd.Series):
        returns = returns.values
    returns = returns[~np.isnan(returns)]

    rng = np.random.default_rng(random_seed)

    # Bootstrap daily returns and compound over the time horizon
    simulated_returns = np.zeros(n_simulations)
    for i in range(n_simulations):
        path = rng.choice(returns, size=time_horizon, replace=True)
        # Compound returns: (1+r1)*(1+r2)*...*(1+rT) - 1
        simulated_returns[i] = np.prod(1 + path) - 1

    alpha = 1 - confidence_level
    var = -np.percentile(simulated_returns, alpha * 100)

    tail_losses = -simulated_returns[simulated_returns < -var]
    if len(tail_losses) > 0:
        cvar = tail_losses.mean()
    else:
        cvar = var

    return VaRResult(
        var=var,
        cvar=cvar,
        confidence_level=confidence_level,
        method=VaRMethod.MONTE_CARLO,
        time_horizon=time_horizon,
    )


# ─── Cornish-Fisher VaR ───────────────────────────────────────────────────────

def var_cornish_fisher(
    returns: pd.Series | np.ndarray,
    confidence_level: float = 0.95,
    time_horizon: int = 1,
) -> VaRResult:
    """
    Cornish-Fisher expansion VaR/CVaR.

    Adjusts parametric VaR for skewness and kurtosis in the return distribution.
    More accurate than plain parametric when returns are non-normal.

    References
    ----------
    Favre, L., & Galeano, J. A. (2002). "Mean-Modified Value-at-Risk Optimization
    with Hedge Funds." Journal of Alternative Investments, 5(2), 21-25.
    """
    require_probability(confidence_level, "confidence_level")
    require_positive(time_horizon, "time_horizon")

    if isinstance(returns, pd.Series):
        returns_series = returns
        returns = returns.values
    else:
        returns_series = pd.Series(returns)
    returns = returns[~np.isnan(returns)]

    mu = returns.mean()
    sigma = returns.std(ddof=1)
    skew = returns_series.skew()
    kurt = returns_series.kurtosis()  # excess kurtosis

    # Scale for time horizon
    mu_scaled = mu * time_horizon
    sigma_scaled = sigma * math.sqrt(time_horizon)

    alpha = 1 - confidence_level
    z = norm.ppf(alpha)

    # Cornish-Fisher adjustment
    z_cf = (
        z
        + (z**2 - 1) * skew / 6
        + (z**3 - 3 * z) * kurt / 24
        - (2 * z**3 - 5 * z) * skew**2 / 36
    )

    var = -(mu_scaled + z_cf * sigma_scaled)

    # CVaR approximation (use parametric formula with adjusted z)
    cvar = var + sigma_scaled * norm.pdf(z_cf) / alpha

    return VaRResult(
        var=var,
        cvar=cvar,
        confidence_level=confidence_level,
        method=VaRMethod.CORNISH_FISHER,
        time_horizon=time_horizon,
    )


# ─── Unified interface ────────────────────────────────────────────────────────

def calculate_var(
    returns: pd.Series | np.ndarray,
    confidence_level: float = 0.95,
    time_horizon: int = 1,
    method: VaRMethod = VaRMethod.HISTORICAL,
    portfolio_value: Optional[float] = None,
    **kwargs,
) -> VaRResult:
    """
    Calculate VaR and CVaR using the specified method.

    Parameters
    ----------
    method : VaRMethod
        Calculation method (HISTORICAL, PARAMETRIC, MONTE_CARLO, CORNISH_FISHER)
    portfolio_value : float, optional
        Current portfolio value in dollars (for dollar VaR reporting)
    **kwargs
        Method-specific parameters (e.g., n_simulations for Monte Carlo)

    Returns
    -------
    VaRResult
        Contains var, cvar, confidence_level, method, and optional dollar values
    """
    if method == VaRMethod.HISTORICAL:
        result = var_historical(returns, confidence_level, time_horizon)
    elif method == VaRMethod.PARAMETRIC:
        result = var_parametric(returns, confidence_level, time_horizon, **kwargs)
    elif method == VaRMethod.MONTE_CARLO:
        result = var_monte_carlo(returns, confidence_level, time_horizon, **kwargs)
    elif method == VaRMethod.CORNISH_FISHER:
        result = var_cornish_fisher(returns, confidence_level, time_horizon)
    else:
        raise ValueError(f"Unknown VaR method: {method}")

    if portfolio_value is not None:
        result.portfolio_value = portfolio_value

    return result
