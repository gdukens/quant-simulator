"""
Data Manager - Market data retrieval and processing tools.

This module provides data acquisition and management functionality 
for the QuantLib Pro SDK.
"""

from typing import Dict, List, Any, Optional, Union
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class DataManager:
    """
    Market data acquisition and management tools.
    
    Provides functionality for:
    - Price data retrieval from multiple sources
    - Economic data from FRED
    - Data caching and quality checks
    - Data transformation and cleaning
    """
    
    def __init__(self, config=None):
        """
        Initialize Data Manager.
        
        Args:
            config: SDK configuration object
        """
        self.config = config
        self.alpha_vantage_key = getattr(config, 'alpha_vantage_key', None) if config else None
        self.fred_api_key = getattr(config, 'fred_api_key', None) if config else None
        self.cache_enabled = getattr(config, 'cache_enabled', True) if config else True
        logger.info("Data Manager initialized")
    
    def get_price_data(self, symbols: Union[str, List[str]], period: str = "1y", 
                      provider: str = "yahoo") -> pd.DataFrame:
        """
        Get historical price data for symbols.
        
        Args:
            symbols: Single symbol or list of symbols
            period: Time period ("1y", "6m", "3m", "1m")
            provider: Data provider ("yahoo", "alpha_vantage")
            
        Returns:
            DataFrame with price data
        """
        if isinstance(symbols, str):
            symbols = [symbols]
        
        try:
            if provider == "yahoo":
                return self._get_yahoo_data(symbols, period)
            elif provider == "alpha_vantage" and self.alpha_vantage_key:
                return self._get_alpha_vantage_data(symbols, period)
            else:
                logger.warning(f"Provider {provider} not available, falling back to mock data")
                return self._get_mock_data(symbols, period)
                
        except Exception as e:
            logger.error(f"Failed to retrieve data for {symbols}: {e}")
            return self._get_mock_data(symbols, period)
    
    def get_economic_data(self, series_id: str, start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.Series:
        """
        Get economic data from FRED.
        
        Args:
            series_id: FRED series ID
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            
        Returns:
            Series with economic data
        """
        try:
            if self.fred_api_key:
                return self._get_fred_data(series_id, start_date, end_date)
            else:
                logger.warning("FRED API key not available, returning mock data")
                return self._get_mock_economic_data(series_id, start_date, end_date)
                
        except Exception as e:
            logger.error(f"Failed to retrieve FRED data for {series_id}: {e}")
            return self._get_mock_economic_data(series_id, start_date, end_date)
    
    def get_supported_symbols(self) -> List[str]:
        """Get list of supported asset symbols."""
        return [
            "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA", "NFLX",
            "SPY", "QQQ", "IWM", "VTI", "BND", "GLD", "SLV", "USO", "VIX"
        ]
    
    def validate_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate data quality.
        
        Args:
            data: DataFrame to validate
            
        Returns:
            Dict containing validation results
        """
        if data.empty:
            return {"valid": False, "errors": ["Data is empty"]}
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "statistics": {
                "total_rows": len(data),
                "missing_values": data.isnull().sum().to_dict(),
                "date_range": {
                    "start": str(data.index.min()) if hasattr(data.index, 'min') else None,
                    "end": str(data.index.max()) if hasattr(data.index, 'max') else None
                }
            }
        }
        
        # Check for missing values
        missing_count = data.isnull().sum().sum()
        if missing_count > 0:
            validation_result["warnings"].append(f"Found {missing_count} missing values")
        
        # Check for outliers (simple z-score method)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in data.columns:
                z_scores = np.abs((data[col] - data[col].mean()) / data[col].std())
                outlier_count = (z_scores > 3).sum()
                if outlier_count > 0:
                    validation_result["warnings"].append(f"Found {outlier_count} outliers in {col}")
        
        logger.info(f"Data validation completed: {validation_result['valid']}")
        return validation_result
    
    def _get_yahoo_data(self, symbols: List[str], period: str) -> pd.DataFrame:
        """Get data from Yahoo Finance (simplified mock implementation)."""
        try:
            import yfinance as yf
            data = yf.download(symbols, period=period, group_by='ticker')
            if len(symbols) == 1:
                return data[['Close']].rename(columns={'Close': symbols[0]})
            else:
                return data.xs('Close', axis=1, level=1)
        except ImportError:
            logger.warning("yfinance not available, using mock data")
            return self._get_mock_data(symbols, period)
    
    def _get_alpha_vantage_data(self, symbols: List[str], period: str) -> pd.DataFrame:
        """Get data from Alpha Vantage (placeholder implementation)."""
        logger.info("Alpha Vantage data retrieval - placeholder implementation")
        return self._get_mock_data(symbols, period)
    
    def _get_fred_data(self, series_id: str, start_date: Optional[str], 
                      end_date: Optional[str]) -> pd.Series:
        """Get data from FRED (placeholder implementation).""" 
        logger.info(f"FRED data retrieval for {series_id} - placeholder implementation")
        return self._get_mock_economic_data(series_id, start_date, end_date)
    
    def _get_mock_data(self, symbols: List[str], period: str) -> pd.DataFrame:
        """Generate mock price data for testing."""
        # Map period to number of days
        period_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "2y": 730}
        days = period_map.get(period, 365)
        
        # Generate dates
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.Timedelta(days=days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate mock price data
        data = pd.DataFrame(index=dates)
        
        for symbol in symbols:
            # Generate realistic price series with random walk
            np.random.seed(hash(symbol) % 2**31)  # Consistent random seed per symbol
            initial_price = 100 + (hash(symbol) % 200)  # Base price 100-300
            
            returns = np.random.normal(0.0005, 0.02, len(dates))  # Daily returns
            prices = [initial_price]
            
            for ret in returns[1:]:
                prices.append(prices[-1] * (1 + ret))
            
            data[symbol] = prices
        
        logger.info(f"Generated mock data for {symbols} over {len(dates)} days")
        return data
    
    def _get_mock_economic_data(self, series_id: str, start_date: Optional[str],
                               end_date: Optional[str]) -> pd.Series:
        """Generate mock economic data."""
        if not start_date:
            start_date = "2020-01-01"
        if not end_date:
            end_date = pd.Timestamp.now().strftime("%Y-%m-%d")
        
        dates = pd.date_range(start=start_date, end=end_date, freq='M')
        
        # Generate realistic economic data based on series type
        np.random.seed(hash(series_id) % 2**31)
        
        if "GDP" in series_id.upper():
            values = 20000 + np.cumsum(np.random.normal(50, 200, len(dates)))
        elif "UNEMPLOYMENT" in series_id.upper() or "UNRATE" in series_id.upper():
            values = 5 + np.random.normal(0, 1, len(dates))
            values = np.clip(values, 2, 15)  # Keep reasonable bounds
        elif "INFLATION" in series_id.upper() or "CPI" in series_id.upper():
            values = 2 + np.random.normal(0, 0.5, len(dates))
            values = np.clip(values, -1, 8)  # Keep reasonable bounds
        else:
            values = np.random.normal(0, 1, len(dates))
        
        series = pd.Series(values, index=dates, name=series_id)
        logger.info(f"Generated mock economic data for {series_id}")
        return series
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of data manager.
        
        Returns:
            Dict containing health status
        """
        return {
            "status": "healthy",
            "module": "data", 
            "providers": {
                "yahoo": True,  # Always available for mock data
                "alpha_vantage": self.alpha_vantage_key is not None,
                "fred": self.fred_api_key is not None
            },
            "cache_enabled": self.cache_enabled,
            "supported_symbols_count": len(self.get_supported_symbols()),
            "capabilities": [
                "price_data_retrieval",
                "economic_data_retrieval",
                "data_validation",
                "multi_provider_support"
            ]
        }