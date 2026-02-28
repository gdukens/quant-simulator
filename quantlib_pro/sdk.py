"""
QuantLib Pro SDK - Enterprise Quantitative Finance Toolkit

This module provides the main SDK interface for QuantLib Pro, offering
a comprehensive suite of quantitative finance tools and utilities.

Usage:
    >>> from quantlib_pro import QuantLibSDK
    >>> sdk = QuantLibSDK()
    >>> 
    >>> # Portfolio analysis
    >>> portfolio = sdk.portfolio.create_portfolio(assets=['AAPL', 'GOOGL'])
    >>> returns = sdk.portfolio.calculate_returns(portfolio)
    >>> 
    >>> # Risk management
    >>> var = sdk.risk.calculate_var(returns, confidence_level=0.05)
    >>> cvar = sdk.risk.calculate_cvar(returns, confidence_level=0.05)
    >>> 
    >>> # Options pricing
    >>> bs_price = sdk.options.black_scholes(S=100, K=105, T=0.25, r=0.05, sigma=0.2)
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import pandas as pd

# Configure logging for SDK
logger = logging.getLogger(__name__)


@dataclass
class SDKConfig:
    """Configuration class for QuantLib Pro SDK."""
    
    # Data source configuration
    alpha_vantage_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    factset_username: Optional[str] = None
    factset_key: Optional[str] = None
    
    # Database configuration
    database_url: Optional[str] = None
    redis_url: Optional[str] = None
    
    # Performance settings
    enable_caching: bool = True
    cache_ttl: int = 3600
    max_workers: int = 4
    
    # Risk management defaults
    default_confidence_level: float = 0.05
    default_time_horizon: int = 252  # Trading days in a year
    
    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    def __post_init__(self):
        """Load configuration from environment variables."""
        self.alpha_vantage_key = self.alpha_vantage_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        self.fred_api_key = self.fred_api_key or os.getenv("FRED_API_KEY") 
        self.factset_username = self.factset_username or os.getenv("FACTSET_USERNAME")
        self.factset_key = self.factset_key or os.getenv("FACTSET_API_KEY")
        self.database_url = self.database_url or os.getenv("DATABASE_URL", "postgresql://quantlib:quantlib123@localhost:5432/quantlib")
        self.redis_url = self.redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")


class QuantLibSDK:
    """
    Main SDK interface for QuantLib Pro.
    
    This class provides access to all quantitative finance modules
    including portfolio management, risk analysis, options pricing,
    volatility modeling, market regime detection, and more.
    
    Args:
        config: Optional SDKConfig instance for custom configuration
        
    Example:
        >>> sdk = QuantLibSDK()
        >>> portfolio_metrics = sdk.portfolio.analyze(['AAPL', 'GOOGL', 'MSFT'])
        >>> risk_metrics = sdk.risk.portfolio_risk(portfolio_metrics)
    """
    
    def __init__(self, config: Optional[SDKConfig] = None):
        self.config = config or SDKConfig()
        self._setup_logging()
        
        # Lazy-loaded managers
        self._portfolio_manager = None
        self._risk_manager = None
        self._options_manager = None
        self._volatility_manager = None
        self._data_manager = None
        self._macro_manager = None
        self._market_regime_manager = None
        self._analytics_manager = None
        self._execution_manager = None
        
        logger.info("QuantLib Pro SDK initialized")
    
    def _setup_logging(self):
        """Configure logging for the SDK."""
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            filename=self.config.log_file
        )
    
    @property
    def portfolio(self):
        """Portfolio management and analysis tools."""
        if self._portfolio_manager is None:
            from .portfolio.manager import PortfolioManager
            self._portfolio_manager = PortfolioManager(self.config)
        return self._portfolio_manager
    
    @property
    def risk(self):
        """Risk management and measurement tools."""
        if self._risk_manager is None:
            from .risk.manager import RiskManager
            self._risk_manager = RiskManager(self.config)
        return self._risk_manager
    
    @property 
    def options(self):
        """Options pricing and Greeks calculation tools."""
        if self._options_manager is None:
            from .options.manager import OptionsManager
            self._options_manager = OptionsManager(self.config)
        return self._options_manager
    
    @property
    def volatility(self):
        """Volatility modeling and forecasting tools."""
        if self._volatility_manager is None:
            from .volatility.manager import VolatilityManager
            self._volatility_manager = VolatilityManager(self.config)
        return self._volatility_manager
    
    @property
    def data(self):
        """Market data retrieval and processing tools."""
        if self._data_manager is None:
            from .data.manager import DataManager
            self._data_manager = DataManager(self.config)
        return self._data_manager
    
    @property
    def macro(self):
        """Macroeconomic analysis and indicators."""
        if self._macro_manager is None:
            from .macro.manager import MacroManager
            self._macro_manager = MacroManager(self.config)
        return self._macro_manager
    
    @property
    def market_regime(self):
        """Market regime detection and analysis."""
        if self._market_regime_manager is None:
            from .market_regime.manager import MarketRegimeManager
            self._market_regime_manager = MarketRegimeManager(self.config)
        return self._market_regime_manager
    
    @property
    def analytics(self):
        """Advanced analytics and statistical tools."""
        if self._analytics_manager is None:
            from .analytics.manager import AnalyticsManager
            self._analytics_manager = AnalyticsManager(self.config)
        return self._analytics_manager
    
    @property
    def execution(self):
        """Trade execution and transaction cost analysis."""
        if self._execution_manager is None:
            from .execution.manager import ExecutionManager
            self._execution_manager = ExecutionManager(self.config)
        return self._execution_manager
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of all SDK components.
        
        Returns:
            Dict containing status of each component
        """
        status = {
            "sdk_version": "1.0.0",
            "config": self.config.__dict__,
            "components": {}
        }
        
        components = [
            ("portfolio", self.portfolio),
            ("risk", self.risk), 
            ("options", self.options),
            ("volatility", self.volatility),
            ("data", self.data),
            ("macro", self.macro),
            ("market_regime", self.market_regime),
            ("analytics", self.analytics),
            ("execution", self.execution)
        ]
        
        for name, component in components:
            try:
                # Test basic functionality if health_check method exists
                if hasattr(component, 'health_check'):
                    status["components"][name] = component.health_check()
                else:
                    status["components"][name] = {"status": "available"}
            except Exception as e:
                status["components"][name] = {"status": "error", "error": str(e)}
                logger.error(f"Health check failed for {name}: {e}")
        
        return status
    
    def get_supported_assets(self) -> List[str]:
        """Get list of supported asset symbols."""
        return self.data.get_supported_symbols()
    
    def quick_analysis(self, symbols: List[str], period: str = "1y") -> Dict[str, Any]:
        """
        Perform quick analysis on a list of symbols.
        
        Args:
            symbols: List of asset symbols to analyze
            period: Time period for analysis (e.g., "1y", "6m", "3m")
            
        Returns:
            Dict containing portfolio and risk metrics
        """
        try:
            # Get data
            data = self.data.get_price_data(symbols, period=period)
            
            # Portfolio analysis
            portfolio_metrics = self.portfolio.calculate_portfolio_metrics(data)
            
            # Risk analysis
            risk_metrics = self.risk.calculate_portfolio_risk(data)
            
            # Combine results
            return {
                "symbols": symbols,
                "period": period,
                "portfolio": portfolio_metrics,
                "risk": risk_metrics,
                "analysis_timestamp": str(pd.Timestamp.now())
            }
            
        except Exception as e:
            logger.error(f"Quick analysis failed: {e}")
            return {"error": str(e)}


# Convenience function for quick SDK access
def create_sdk(config: Optional[Dict[str, Any]] = None) -> QuantLibSDK:
    """
    Convenience function to create a QuantLibSDK instance.
    
    Args:
        config: Dictionary of configuration parameters
        
    Returns:
        Configured QuantLibSDK instance
    """
    if config:
        sdk_config = SDKConfig(**config)
    else:
        sdk_config = SDKConfig()
    
    return QuantLibSDK(sdk_config)


# Version information
__version__ = "1.0.0"
__author__ = "QuantLib Pro Team"
__email__ = "info@quantlibpro.com"

# Package-level exports
__all__ = [
    "QuantLibSDK",
    "SDKConfig", 
    "create_sdk",
    "__version__",
    "__author__", 
    "__email__"
]