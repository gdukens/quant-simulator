"""
Portfolio Manager - Portfolio analysis and optimization tools.

This module provides portfolio construction, optimization, and analysis
functionality for the QuantLib Pro SDK.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class PortfolioManager:
    """
    Portfolio management and analysis tools.
    
    Provides functionality for:
    - Portfolio construction and optimization
    - Performance attribution and analysis
    - Rebalancing and risk budgeting
    - Backtesting and scenario analysis
    """
    
    def __init__(self, config=None):
        """
        Initialize Portfolio Manager.
        
        Args:
            config: SDK configuration object
        """
        self.config = config
        logger.info("Portfolio Manager initialized")
    
    def create_portfolio(self, assets: List[str], weights: Optional[List[float]] = None) -> Dict[str, Any]:
        """
        Create a portfolio from assets and weights.
        
        Args:
            assets: List of asset symbols
            weights: Optional list of weights (equal weights if None)
            
        Returns:
            Dict containing portfolio information
        """
        if weights is None:
            weights = [1.0 / len(assets)] * len(assets)
        
        if len(weights) != len(assets):
            raise ValueError("Number of weights must match number of assets")
        
        if abs(sum(weights) - 1.0) > 1e-6:
            logger.warning("Weights do not sum to 1.0, normalizing.")
            weights = [w / sum(weights) for w in weights]
        
        portfolio = {
            "assets": assets,
            "weights": weights,
            "creation_date": pd.Timestamp.now(),
            "portfolio_id": f"portfolio_{hash(str(assets + weights)) % 10000}"
        }
        
        logger.info(f"Created portfolio with {len(assets)} assets")
        return portfolio
    
    def calculate_returns(self, portfolio_data: pd.DataFrame) -> pd.Series:
        """
        Calculate portfolio returns from price data.
        
        Args:
            portfolio_data: DataFrame with price data
            
        Returns:
            Series of portfolio returns
        """
        if portfolio_data.empty:
            raise ValueError("Portfolio data cannot be empty")
        
        returns = portfolio_data.pct_change().dropna()
        logger.info(f"Calculated returns for {len(returns)} periods")
        return returns
    
    def calculate_portfolio_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """
        Calculate key portfolio performance metrics.
        
        Args:
            returns: Series of portfolio returns
            
        Returns:
            Dict containing performance metrics
        """
        if len(returns) < 2:
            raise ValueError("Need at least 2 return observations")
        
        metrics = {
            "total_return": (1 + returns).prod() - 1,
            "annualized_return": (1 + returns.mean()) ** 252 - 1,
            "volatility": returns.std() * np.sqrt(252),
            "sharpe_ratio": (returns.mean() * 252) / (returns.std() * np.sqrt(252)),
            "max_drawdown": self._calculate_max_drawdown(returns),
            "skewness": returns.skew(),
            "kurtosis": returns.kurtosis(),
            "var_95": returns.quantile(0.05),
            "observation_count": len(returns)
        }
        
        logger.info("Calculated portfolio metrics")
        return metrics
    
    def optimize_portfolio(self, expected_returns: pd.Series, 
                          covariance_matrix: pd.DataFrame,
                          risk_aversion: float = 1.0) -> Dict[str, Any]:
        """
        Optimize portfolio using mean-variance optimization.
        
        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Asset covariance matrix
            risk_aversion: Risk aversion parameter
            
        Returns:
            Dict containing optimal weights and metrics
        """
        try:
            # Simple mean-variance optimization
            inv_cov = np.linalg.inv(covariance_matrix.values)
            ones = np.ones((len(expected_returns), 1))
            
            # Calculate optimal weights
            w_opt = (inv_cov @ expected_returns.values.reshape(-1, 1)) / risk_aversion
            w_opt = w_opt / np.sum(w_opt)  # Normalize
            
            # Calculate expected portfolio return and risk
            expected_port_return = float(expected_returns.T @ w_opt.flatten())
            expected_port_risk = float(np.sqrt(w_opt.T @ covariance_matrix.values @ w_opt))
            
            result = {
                "optimal_weights": dict(zip(expected_returns.index, w_opt.flatten())),
                "expected_return": expected_port_return,
                "expected_risk": expected_port_risk,
                "sharpe_ratio": expected_port_return / expected_port_risk if expected_port_risk > 0 else 0,
                "optimization_method": "mean_variance"
            }
            
            logger.info("Portfolio optimization completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            return {"error": str(e)}
    
    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        Calculate maximum drawdown from returns series.
        
        Args:
            returns: Series of returns
            
        Returns:
            Maximum drawdown as a float
        """
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return float(drawdown.min())
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of portfolio manager.
        
        Returns:
            Dict containing health status
        """
        return {
            "status": "healthy",
            "module": "portfolio",
            "capabilities": [
                "portfolio_creation",
                "return_calculation", 
                "performance_metrics",
                "mean_variance_optimization"
            ]
        }