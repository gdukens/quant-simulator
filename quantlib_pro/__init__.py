"""
QuantLib Pro SDK — Unified Quantitative Finance Suite
==================================================
Enterprise-grade quantitative finance toolkit for Python

Quick Start:
    >>> from quantlib_pro import QuantLibSDK
    >>> sdk = QuantLibSDK()
    >>> 
    >>> # Portfolio Analysis
    >>> portfolio = sdk.portfolio.create(['AAPL', 'GOOGL', 'MSFT'])
    >>> weights = sdk.portfolio.optimize(portfolio)
    >>> 
    >>> # Risk Calculations
    >>> var = sdk.risk.value_at_risk(portfolio, confidence=0.95)
    >>> 
    >>> # Options Pricing
    >>> price = sdk.options.black_scholes(100, 105, 0.25, 0.02, 0.2)

Modules:
    A: Options Pricing & Derivatives (sdk.options)
    B: Risk Analysis & Metrics (sdk.risk)  
    C: Portfolio Management & Optimization (sdk.portfolio)
    D: Market Regime Detection (sdk.market_regime)
    E: Execution & Market Microstructure (sdk.execution)
    F: Volatility Analysis (sdk.volatility)
    G: Macro & Economic Data (sdk.macro)
"""

__version__ = "1.0.0"
__author__ = "QuantLib Pro Team"
__license__ = "MIT"

# Core SDK imports
from typing import Dict, Any, Optional, List
import logging
from dataclasses import dataclass, field

# Configure package logging
logger = logging.getLogger(__name__)


@dataclass
class SDKConfig:
    """SDK Configuration with sensible defaults"""
    # API Keys
    fred_api_key: Optional[str] = None
    alpha_vantage_key: Optional[str] = None
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl: int = 3600
    
    # Financial defaults
    risk_free_rate: float = 0.02
    default_currency: str = "USD"
    
    # System settings
    debug_mode: bool = False
    max_workers: int = 4


class QuantLibSDK:
    """
    QuantLib Pro SDK - Main Interface
    
    Enterprise quantitative finance toolkit providing:
    - Portfolio optimization & risk management
    - Options pricing & Greeks calculation
    - Market regime detection & analysis  
    - Volatility modeling & forecasting
    - Economic data integration (FRED)
    - Backtesting & strategy validation
    """
    
    def __init__(self, config: Optional[SDKConfig] = None, **kwargs):
        """
        Initialize QuantLib Pro SDK
        
        Args:
            config: SDK configuration object
            **kwargs: Direct configuration parameters
        """
        self.config = config or SDKConfig()
        
        # Update config with any direct parameters
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Lazy loading - modules initialized on first access
        self._portfolio = None
        self._risk = None
        self._options = None
        self._volatility = None
        self._data = None
        self._macro = None
        self._market_regime = None
        self._analytics = None
        self._execution = None
        
        logger.info(f"QuantLib Pro SDK v{__version__} initialized")
    
    @property
    def portfolio(self):
        """Portfolio optimization and management"""
        if self._portfolio is None:
            from .portfolio import PortfolioManager
            self._portfolio = PortfolioManager(self.config)
        return self._portfolio
    
    @property  
    def risk(self):
        """Risk analysis and VaR calculations"""
        if self._risk is None:
            from .risk import RiskManager
            self._risk = RiskManager(self.config)
        return self._risk
    
    @property
    def options(self):
        """Options pricing and Greeks"""
        if self._options is None:
            from .options import OptionsManager
            self._options = OptionsManager(self.config)
        return self._options
    
    @property
    def volatility(self):
        """Volatility modeling and analysis"""
        if self._volatility is None:
            from .volatility import VolatilityManager
            self._volatility = VolatilityManager(self.config) 
        return self._volatility
    
    @property
    def data(self):
        """Market data acquisition and management"""
        if self._data is None:
            from .data import DataManager
            self._data = DataManager(self.config)
        return self._data
    
    @property
    def macro(self):
        """Macroeconomic data and analysis"""
        if self._macro is None:
            from .macro import MacroManager
            self._macro = MacroManager(self.config)
        return self._macro
    
    @property
    def market_regime(self):
        """Market regime detection and analysis"""
        if self._market_regime is None:
            from .market_regime import MarketRegimeManager
            self._market_regime = MarketRegimeManager(self.config)
        return self._market_regime
    
    @property
    def analytics(self):
        """Advanced analytics and modeling"""
        if self._analytics is None:
            from .analytics import AnalyticsManager
            self._analytics = AnalyticsManager(self.config)
        return self._analytics
    
    @property
    def execution(self):
        """Execution and market microstructure"""
        if self._execution is None:
            from .execution import ExecutionManager
            self._execution = ExecutionManager(self.config)
        return self._execution
    
    def health_check(self) -> Dict[str, Any]:
        """Check SDK health status"""
        return {
            "sdk_version": __version__,
            "status": "healthy",
            "config": {
                "cache_enabled": self.config.cache_enabled,
                "risk_free_rate": self.config.risk_free_rate,
                "currency": self.config.default_currency
            }
        }
    
    def get_version(self) -> str:
        """Get SDK version"""
        return __version__


# Convenience imports for direct access
try:
    from .utils.logging import get_logger
except ImportError:
    # Fallback if logging utils not available
    import logging
    get_logger = logging.getLogger

# Public API
__all__ = [
    "QuantLibSDK",
    "SDKConfig", 
    "__version__",
    "__author__",
    "get_logger"
]
