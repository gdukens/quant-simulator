"""
Risk Manager - Risk analysis and measurement tools.

This module provides risk management functionality including VaR calculation,
stress testing, and risk attribution for the QuantLib Pro SDK.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Risk management and measurement tools.
    
    Provides functionality for:
    - Value at Risk (VaR) calculations
    - Expected Shortfall (CVaR) 
    - Stress testing and scenario analysis
    - Risk attribution and decomposition
    - Correlation and volatility analysis
    """
    
    def __init__(self, config=None):
        """
        Initialize Risk Manager.
        
        Args:
            config: SDK configuration object
        """
        self.config = config
        self.default_confidence_level = getattr(config, 'default_confidence_level', 0.05) if config else 0.05
        logger.info("Risk Manager initialized")
    
    def calculate_var(self, returns: pd.Series, confidence_level: float = None, 
                      method: str = "historical") -> float:
        """
        Calculate Value at Risk (VaR).
        
        Args:
            returns: Series of portfolio returns
            confidence_level: Confidence level (default from config)
            method: VaR calculation method ("historical", "parametric", "monte_carlo")
            
        Returns:
            VaR as a float (positive value represents loss)
        """
        if confidence_level is None:
            confidence_level = self.default_confidence_level
            
        if len(returns) < 10:
            raise ValueError("Need at least 10 return observations for VaR calculation")
        
        if method == "historical":
            var = -returns.quantile(confidence_level)
        elif method == "parametric":
            # Assuming normal distribution
            mean_return = returns.mean()
            std_return = returns.std()
            var = -(mean_return + stats.norm.ppf(confidence_level) * std_return)
        elif method == "monte_carlo":
            # Simplified Monte Carlo (normally would use more sophisticated methods)
            simulated_returns = np.random.normal(returns.mean(), returns.std(), 10000)
            var = -np.percentile(simulated_returns, confidence_level * 100)
        else:
            raise ValueError(f"Unknown VaR method: {method}")
        
        logger.info(f"Calculated {method} VaR: {var:.4f} at {confidence_level:.1%} confidence")
        return float(var)
    
    def calculate_cvar(self, returns: pd.Series, confidence_level: float = None) -> float:
        """
        Calculate Conditional Value at Risk (Expected Shortfall).
        
        Args:
            returns: Series of portfolio returns
            confidence_level: Confidence level (default from config)
            
        Returns:
            CVaR as a float (positive value represents expected loss)
        """
        if confidence_level is None:
            confidence_level = self.default_confidence_level
            
        if len(returns) < 10:
            raise ValueError("Need at least 10 return observations for CVaR calculation")
        
        # Calculate VaR threshold
        var_threshold = returns.quantile(confidence_level)
        
        # Calculate expected value of returns below VaR threshold
        tail_returns = returns[returns <= var_threshold]
        if len(tail_returns) == 0:
            cvar = -var_threshold  # If no observations in tail, use VaR
        else:
            cvar = -tail_returns.mean()
        
        logger.info(f"Calculated CVaR: {cvar:.4f} at {confidence_level:.1%} confidence")
        return float(cvar)
    
    def calculate_portfolio_risk(self, returns_data: pd.DataFrame, 
                               weights: Optional[List[float]] = None) -> Dict[str, float]:
        """
        Calculate comprehensive portfolio risk metrics.
        
        Args:
            returns_data: DataFrame of asset returns
            weights: Optional portfolio weights (equal weights if None)
            
        Returns:
            Dict containing various risk metrics
        """
        if returns_data.empty:
            raise ValueError("Returns data cannot be empty")
        
        # Calculate portfolio returns
        if weights is None:
            weights = [1.0 / len(returns_data.columns)] * len(returns_data.columns)
        
        portfolio_returns = (returns_data * weights).sum(axis=1)
        
        # Calculate risk metrics
        metrics = {
            "portfolio_volatility": portfolio_returns.std() * np.sqrt(252),
            "var_95": self.calculate_var(portfolio_returns, confidence_level=0.05),
            "var_99": self.calculate_var(portfolio_returns, confidence_level=0.01),
            "cvar_95": self.calculate_cvar(portfolio_returns, confidence_level=0.05),
            "cvar_99": self.calculate_cvar(portfolio_returns, confidence_level=0.01),
            "skewness": portfolio_returns.skew(),
            "kurtosis": portfolio_returns.kurtosis(),
            "max_drawdown": self._calculate_max_drawdown(portfolio_returns),
            "downside_deviation": self._calculate_downside_deviation(portfolio_returns),
            "observation_count": len(portfolio_returns)
        }
        
        logger.info("Calculated comprehensive portfolio risk metrics")
        return metrics
    
    def stress_test(self, returns: pd.Series, scenarios: Dict[str, float]) -> Dict[str, float]:
        """
        Perform stress testing on portfolio returns.
        
        Args:
            returns: Series of portfolio returns
            scenarios: Dict of scenario names and shock magnitudes
            
        Returns:
            Dict of scenario results
        """
        results = {}
        base_portfolio_value = 1.0  # Normalized base value
        
        for scenario_name, shock in scenarios.items():
            # Simple linear shock application
            shocked_returns = returns + shock
            final_value = (1 + shocked_returns).prod()
            loss = base_portfolio_value - final_value
            
            results[scenario_name] = {
                "shock_applied": shock,
                "final_portfolio_value": final_value,
                "absolute_loss": loss,
                "percentage_loss": loss / base_portfolio_value * 100
            }
        
        logger.info(f"Completed stress test with {len(scenarios)} scenarios")
        return results
    
    def calculate_correlation_matrix(self, returns_data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate correlation matrix of asset returns.
        
        Args:
            returns_data: DataFrame of asset returns
            
        Returns:
            Correlation matrix as DataFrame
        """
        correlation_matrix = returns_data.corr()
        logger.info(f"Calculated correlation matrix for {len(returns_data.columns)} assets")
        return correlation_matrix
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown from returns series."""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
    
    def _calculate_downside_deviation(self, returns: pd.Series, target_return: float = 0.0) -> float:
        """Calculate downside deviation (downside volatility)."""
        downside_returns = returns[returns < target_return]
        if len(downside_returns) == 0:
            return 0.0
        return float(np.sqrt(((downside_returns - target_return) ** 2).mean()) * np.sqrt(252))
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of risk manager.
        
        Returns:
            Dict containing health status
        """
        return {
            "status": "healthy",
            "module": "risk",
            "default_confidence_level": self.default_confidence_level,
            "capabilities": [
                "var_calculation",
                "cvar_calculation",
                "portfolio_risk_metrics",
                "stress_testing", 
                "correlation_analysis"
            ]
        }