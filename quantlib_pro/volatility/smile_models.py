"""
Parametric volatility smile models.

Implements:
  - SVI (Stochastic Volatility Inspired)
  - SABR (Stochastic Alpha Beta Rho)
  - Polynomial smile models

These models fit market-observed volatility smiles with
a small number of parameters.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy.optimize import minimize

from quantlib_pro.utils.validation import ValidationError, require_positive

log = logging.getLogger(__name__)


@dataclass
class SVIParameters:
    """SVI model parameters."""
    a: float  # ATM level
    b: float  # Variance scaling
    rho: float  # Skew (correlation)
    m: float  # ATM location
    sigma: float  # Curvature
    
    def __post_init__(self):
        # Validate no-arbitrage conditions
        if self.b < 0:
            raise ValidationError("SVI parameter b must be >= 0")
        if not -1 <= self.rho <= 1:
            raise ValidationError("SVI parameter rho must be in [-1, 1]")
        if self.sigma <= 0:
            raise ValidationError("SVI parameter sigma must be > 0")


def svi_total_variance(k: float, params: SVIParameters) -> float:
    """
    SVI total variance formula.
    
    w(k) = a + b * (ρ * (k - m) + sqrt((k - m)² + σ²))
    
    where k = log(K/F) is log-moneyness.
    
    Parameters
    ----------
    k : float
        Log-moneyness log(K/F)
    params : SVIParameters
        SVI parameters
    
    Returns
    -------
    float
        Total variance w(k)
    """
    term = (k - params.m) ** 2 + params.sigma ** 2
    w = params.a + params.b * (params.rho * (k - params.m) + np.sqrt(term))
    return w


def svi_implied_vol(k: float, T: float, params: SVIParameters) -> float:
    """
    SVI implied volatility.
    
    σ(k, T) = sqrt(w(k) / T)
    
    Parameters
    ----------
    k : float
        Log-moneyness
    T : float
        Time to maturity (years)
    params : SVIParameters
        SVI parameters
    
    Returns
    -------
    float
        Implied volatility σ
    """
    w = svi_total_variance(k, params)
    return np.sqrt(w / T) if T > 0 and w >= 0 else 0.0


def fit_svi_smile(
    log_moneyness: np.ndarray,
    implied_vols: np.ndarray,
    maturity: float,
    initial_guess: Optional[SVIParameters] = None,
) -> SVIParameters:
    """
    Fit SVI model to market smile.
    
    Parameters
    ----------
    log_moneyness : np.ndarray
        Log-moneyness values k = log(K/F)
    implied_vols : np.ndarray
        Observed implied volatilities
    maturity : float
        Time to maturity
    initial_guess : SVIParameters, optional
        Initial parameter guess
    
    Returns
    -------
    SVIParameters
        Fitted SVI parameters
    """
    require_positive(maturity, "maturity")
    
    if len(log_moneyness) != len(implied_vols):
        raise ValidationError("log_moneyness and implied_vols must have same length")
    
    # Convert IV to total variance
    total_var_market = implied_vols ** 2 * maturity
    
    # Initial guess
    if initial_guess is None:
        atm_var = np.median(total_var_market)
        initial_guess = SVIParameters(
            a=atm_var * 0.8,
            b=0.1,
            rho=-0.2,
            m=0.0,
            sigma=0.2,
        )
    
    # Objective: minimize squared error
    def objective(params_array):
        try:
            params = SVIParameters(*params_array)
            model_var = np.array([svi_total_variance(k, params) for k in log_moneyness])
            error = np.sum((model_var - total_var_market) ** 2)
            return error
        except:
            return 1e10
    
    # Bounds
    bounds = [
        (0.0, None),  # a >= 0
        (0.0, None),  # b >= 0
        (-0.999, 0.999),  # rho in (-1, 1)
        (None, None),  # m unconstrained
        (0.001, None),  # sigma > 0
    ]
    
    x0 = [initial_guess.a, initial_guess.b, initial_guess.rho, initial_guess.m, initial_guess.sigma]
    
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
    
    if not result.success:
        log.warning(f"SVI fitting failed: {result.message}")
    
    return SVIParameters(*result.x)


@dataclass
class SABRParameters:
    """SABR model parameters."""
    alpha: float  # ATM volatility
    beta: float  # CEV exponent (0 = normal, 1 = lognormal)
    rho: float  # Correlation
    nu: float  # Vol-of-vol
    
    def __post_init__(self):
        if not 0 <= self.beta <= 1:
            raise ValidationError("SABR beta must be in [0, 1]")
        if not -1 <= self.rho <= 1:
            raise ValidationError("SABR rho must be in [-1, 1]")
        if self.nu < 0:
            raise ValidationError("SABR nu must be >= 0")


def sabr_implied_vol(
    K: float,
    F: float,
    T: float,
    params: SABRParameters,
) -> float:
    """
    SABR implied volatility (Hagan et al. 2002 approximation).
    
    Parameters
    ----------
    K : float
        Strike price
    F : float
        Forward price
    T : float
        Time to maturity
    params : SABRParameters
        SABR parameters
    
    Returns
    -------
    float
        Implied volatility σ
    """
    if K <= 0 or F <= 0 or T <= 0:
        return 0.0
    
    alpha = params.alpha
    beta = params.beta
    rho = params.rho
    nu = params.nu
    
    # ATM case
    if abs(K - F) < 1e-6:
        return alpha / (F ** (1 - beta))
    
    # Non-ATM case (Hagan formula)
    FK = F * K
    log_FK = np.log(F / K)
    
    z = (nu / alpha) * (FK ** ((1 - beta) / 2)) * log_FK
    
    # Handle division by zero
    if abs(z) < 1e-6:
        x_z = 1.0
    else:
        x_z = z / np.log((np.sqrt(1 - 2 * rho * z + z ** 2) + z - rho) / (1 - rho))
    
    # First term
    term1 = alpha / ((FK ** ((1 - beta) / 2)) * (1 + ((1 - beta) ** 2 / 24) * (log_FK ** 2) + ((1 - beta) ** 4 / 1920) * (log_FK ** 4)))
    
    # Second term
    term2 = x_z
    
    # Third term (time correction)
    term3 = 1 + T * (
        ((1 - beta) ** 2 / 24) * (alpha ** 2 / (FK ** (1 - beta))) +
        (rho * beta * nu * alpha / (4 * (FK ** ((1 - beta) / 2)))) +
        ((2 - 3 * rho ** 2) / 24) * (nu ** 2)
    )
    
    sigma = term1 * term2 * term3
    return max(sigma, 0.0)


def fit_sabr_smile(
    strikes: np.ndarray,
    implied_vols: np.ndarray,
    forward: float,
    maturity: float,
    beta: float = 0.5,
) -> SABRParameters:
    """
    Fit SABR model to market smile.
    
    Parameters
    ----------
    strikes : np.ndarray
        Strike prices
    implied_vols : np.ndarray
        Market implied volatilities
    forward : float
        Forward price
    maturity : float
        Time to maturity
    beta : float
        Fixed beta parameter (typically 0.5 or 1.0)
    
    Returns
    -------
    SABRParameters
        Fitted SABR parameters
    """
    require_positive(forward, "forward")
    require_positive(maturity, "maturity")
    
    if len(strikes) != len(implied_vols):
        raise ValidationError("strikes and implied_vols must have same length")
    
    # Initial guess
    atm_vol = np.median(implied_vols)
    
    # Objective: minimize squared error
    def objective(params_array):
        alpha, rho, nu = params_array
        if alpha <= 0 or nu < 0 or not -1 <= rho <= 1:
            return 1e10
        
        try:
            params = SABRParameters(alpha=alpha, beta=beta, rho=rho, nu=nu)
            model_vols = np.array([sabr_implied_vol(K, forward, maturity, params) for K in strikes])
            error = np.sum((model_vols - implied_vols) ** 2)
            return error
        except:
            return 1e10
    
    # Bounds
    bounds = [
        (0.001, 2.0),  # alpha
        (-0.999, 0.999),  # rho
        (0.0, 2.0),  # nu
    ]
    
    x0 = [atm_vol, 0.0, 0.3]
    
    result = minimize(objective, x0, bounds=bounds, method='L-BFGS-B')
    
    if not result.success:
        log.warning(f"SABR fitting failed: {result.message}")
    
    alpha, rho, nu = result.x
    return SABRParameters(alpha=alpha, beta=beta, rho=rho, nu=nu)


def polynomial_smile(
    moneyness: np.ndarray,
    atm_vol: float,
    skew: float = 0.0,
    curvature: float = 0.0,
) -> np.ndarray:
    """
    Simple polynomial smile model.
    
    σ(K) = σ_ATM + skew * log(K/F) + curvature * log(K/F)²
    
    Parameters
    ----------
    moneyness : np.ndarray
        K/F moneyness
    atm_vol : float
        ATM volatility
    skew : float
        Linear skew term
    curvature : float
        Quadratic curvature term
    
    Returns
    -------
    np.ndarray
        Implied volatilities
    """
    log_m = np.log(moneyness)
    return atm_vol + skew * log_m + curvature * (log_m ** 2)
