"""Data provider router with automatic fallback.

Provides:
- Primary provider: Alpha Vantage (premium quality, rate limited)
- Fallback provider: Yahoo Finance (unlimited, free)
- Automatic fallback on rate limit or failure
- Unified interface for all data operations

Usage:
    router = DataProviderRouter()
    quote = router.get_quote("AAPL")  # Tries Alpha Vantage, falls back to Yahoo if needed
    history = router.get_historical("AAPL", period="1y")
"""

import logging
from typing import Dict, Any, Optional, List
from enum import Enum

from quantlib_pro.data.alpha_vantage_client import AlphaVantageClient
from quantlib_pro.data.yahoo_client import YahooFinanceClient


logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Data provider status."""
    ACTIVE = "active"
    RATE_LIMITED = "rate_limited"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class DataProviderRouter:
    """Router for market data with automatic provider fallback.
    
    Fallback chain:
    1. Alpha Vantage (if API key available and not rate limited)
    2. Yahoo Finance (unlimited free tier)
    """
    
    def __init__(
        self,
        alpha_vantage_api_key: Optional[str] = None,
        alpha_vantage_tier: str = "free",
        prefer_alpha_vantage: bool = True,
        timeout: int = 10
    ):
        """Initialize data provider router.
        
        Args:
            alpha_vantage_api_key: Alpha Vantage API key (optional)
            alpha_vantage_tier: Alpha Vantage tier (free, basic, premium)
            prefer_alpha_vantage: Prefer Alpha Vantage over Yahoo Finance
            timeout: Request timeout in seconds
        """
        self.prefer_alpha_vantage = prefer_alpha_vantage
        self.timeout = timeout
        
        # Initialize providers
        self.alpha_vantage: Optional[AlphaVantageClient] = None
        self.yahoo: YahooFinanceClient = YahooFinanceClient(timeout=timeout)
        
        # Try to initialize Alpha Vantage
        try:
            self.alpha_vantage = AlphaVantageClient(
                api_key=alpha_vantage_api_key,
                tier=alpha_vantage_tier,
                timeout=timeout
            )
            logger.info(" Alpha Vantage client initialized")
        except ValueError as e:
            logger.warning(f"Alpha Vantage not available: {e}")
            self.alpha_vantage = None
        
        # Provider status tracking
        self.alpha_vantage_status = ProviderStatus.ACTIVE if self.alpha_vantage else ProviderStatus.UNAVAILABLE
        self.yahoo_status = ProviderStatus.ACTIVE
    
    def _try_providers(
        self,
        operation: str,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """Try operation with providers in order, falling back on failure.
        
        Args:
            operation: Method name (e.g., "get_quote")
            *args: Positional arguments for the operation
            **kwargs: Keyword arguments for the operation
        
        Returns:
            Result from the first successful provider
        
        Raises:
            Exception if all providers fail
        """
        providers = []
        
        # Build provider list based on preference
        if self.prefer_alpha_vantage and self.alpha_vantage:
            providers.append(("Alpha Vantage", self.alpha_vantage, self.alpha_vantage_status))
        
        providers.append(("Yahoo Finance", self.yahoo, self.yahoo_status))
        
        if not self.prefer_alpha_vantage and self.alpha_vantage:
            providers.append(("Alpha Vantage", self.alpha_vantage, self.alpha_vantage_status))
        
        errors = []
        
        for provider_name, provider, status in providers:
            # Skip unavailable providers
            if status == ProviderStatus.UNAVAILABLE:
                continue
            
            try:
                # Get the method from the provider
                method = getattr(provider, operation)
                
                logger.debug(f"Trying {provider_name}.{operation}({args[0] if args else ''})")
                result = method(*args, **kwargs)
                
                # Add metadata
                result["_provider"] = provider_name
                result["_timestamp"] = result.get("timestamp", "")
                
                logger.info(f" {provider_name} {operation} succeeded")
                return result
            
            except Exception as e:
                error_msg = str(e)
                logger.warning(f" {provider_name} {operation} failed: {error_msg}")
                errors.append((provider_name, error_msg))
                
                # Update provider status
                if "rate limit" in error_msg.lower() or "429" in error_msg:
                    if provider_name == "Alpha Vantage":
                        self.alpha_vantage_status = ProviderStatus.RATE_LIMITED
                elif "circuit breaker" in error_msg.lower():
                    if provider_name == "Alpha Vantage":
                        self.alpha_vantage_status = ProviderStatus.FAILED
                
                continue
        
        # All providers failed
        error_summary = "; ".join([f"{name}: {msg}" for name, msg in errors])
        raise Exception(f"All providers failed for {operation}: {error_summary}")
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol.
        
        Args:
            symbol: Stock ticker (e.g., "AAPL")
        
        Returns:
            Dict with quote data and provider info
        """
        return self._try_providers("get_quote", symbol)
    
    def get_historical(
        self,
        symbol: str,
        period: str = "1y",
        adjusted: bool = True
    ) -> Dict[str, Any]:
        """Get historical daily prices for a symbol.
        
        Args:
            symbol: Stock ticker
            period: Data period for Yahoo Finance (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            adjusted: Include adjusted close (for dividends/splits)
        
        Returns:
            Dict with time-series data and provider info
        """
        # Alpha Vantage uses outputsize instead of period
        if self.prefer_alpha_vantage and self.alpha_vantage:
            try:
                # Map period to Alpha Vantage outputsize
                outputsize = "full" if period in ["5y", "10y", "max"] else "compact"
                result = self.alpha_vantage.get_historical(
                    symbol,
                    outputsize=outputsize,
                    adjusted=adjusted
                )
                result["_provider"] = "Alpha Vantage"
                return result
            except Exception as e:
                logger.warning(f"Alpha Vantage failed: {e}, falling back to Yahoo Finance")
        
        # Yahoo Finance fallback
        return self._try_providers("get_historical", symbol, period=period, adjusted=adjusted)
    
    def get_intraday(
        self,
        symbol: str,
        interval: str = "5m"
    ) -> Dict[str, Any]:
        """Get intraday prices.
        
        Args:
            symbol: Stock ticker
            interval: Time interval (1m, 5m, 15m, 30m, 60m)
        
        Returns:
            Dict with intraday time-series data and provider info
        
        Note:
            Intraday data may only be available with premium Alpha Vantage or
            for limited periods on Yahoo Finance (1m data: 7 days only)
        """
        return self._try_providers("get_intraday", symbol, interval=interval)
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get quotes for multiple symbols.
        
        Args:
            symbols: List of stock tickers
        
        Returns:
            Dict mapping symbol to quote data: {
                "AAPL": {...},
                "MSFT": {...},
                ...
            }
        """
        results = {}
        errors = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_quote(symbol)
            except Exception as e:
                logger.error(f"Failed to get quote for {symbol}: {e}")
                errors[symbol] = str(e)
        
        if errors:
            logger.warning(f"Batch quote errors: {errors}")
        
        return results
    
    def get_batch_historical(
        self,
        symbols: List[str],
        period: str = "1y",
        adjusted: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Get historical data for multiple symbols.
        
        Args:
            symbols: List of stock tickers
            period: Data period
            adjusted: Include adjusted close
        
        Returns:
            Dict mapping symbol to historical data
        """
        results = {}
        errors = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_historical(symbol, period=period, adjusted=adjusted)
            except Exception as e:
                logger.error(f"Failed to get historical data for {symbol}: {e}")
                errors[symbol] = str(e)
        
        if errors:
            logger.warning(f"Batch historical errors: {errors}")
        
        return results
    
    def get_provider_status(self) -> Dict[str, str]:
        """Get status of all providers.
        
        Returns:
            Dict with provider statuses: {
                "alpha_vantage": "active",
                "yahoo_finance": "active"
            }
        """
        return {
            "alpha_vantage": self.alpha_vantage_status.value,
            "yahoo_finance": self.yahoo_status.value
        }
    
    def reset_alpha_vantage_status(self):
        """Reset Alpha Vantage status (for manual recovery)."""
        if self.alpha_vantage:
            self.alpha_vantage_status = ProviderStatus.ACTIVE
            logger.info("Alpha Vantage status reset to ACTIVE")
    
    def close(self):
        """Close all provider connections."""
        if self.alpha_vantage:
            self.alpha_vantage.close()
        # Yahoo Finance client doesn't need explicit close
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
