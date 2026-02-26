"""Yahoo Finance API client (fallback provider).

Features:
- Unlimited free data access
- No API key required
- Historical and real-time quotes
- Dividend and split-adjusted data
- Fallback when Alpha Vantage rate limits are hit

Library: yfinance (https://github.com/ranaroussi/yfinance)
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd


logger = logging.getLogger(__name__)


class YahooFinanceClient:
    """Yahoo Finance API client (unlimited free tier)."""
    
    def __init__(self, timeout: int = 10):
        """Initialize Yahoo Finance client.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
    
    def get_quote(self, symbol: str) -> Dict[str, Any]:
        """Get real-time quote for a symbol.
        
        Args:
            symbol: Stock ticker (e.g., "AAPL")
        
        Returns:
            Dict with quote data: {
                "symbol": "AAPL",
                "price": 150.25,
                "volume": 100000000,
                "timestamp": "2025-01-16 16:00:00"
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get fast info (more reliable)
            fast_info = ticker.fast_info
            
            return {
                "symbol": symbol.upper(),
                "price": fast_info.get("last_price", info.get("currentPrice", 0)),
                "volume": fast_info.get("last_volume", info.get("volume", 0)),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "change": info.get("regularMarketChange", 0),
                "change_percent": info.get("regularMarketChangePercent", 0),
                "open": info.get("regularMarketOpen", 0),
                "high": info.get("dayHigh", 0),
                "low": info.get("dayLow", 0),
                "previous_close": info.get("previousClose", 0),
            }
        
        except Exception as e:
            logger.error(f"Yahoo Finance quote error for {symbol}: {e}")
            raise ValueError(f"Failed to get quote for {symbol}: {e}")
    
    def get_historical(
        self,
        symbol: str,
        period: str = "max",  # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
        interval: str = "1d",  # 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo
        start: Optional[str] = None,
        end: Optional[str] = None,
        adjusted: bool = True
    ) -> Dict[str, Any]:
        """Get historical daily prices for a symbol.
        
        Args:
            symbol: Stock ticker
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            start: Start date (YYYY-MM-DD) - overrides period
            end: End date (YYYY-MM-DD)
            adjusted: Include adjusted close (for dividends/splits)
        
        Returns:
            Dict with time-series data: {
                "symbol": "AAPL",
                "data": [
                    {"date": "2025-01-16", "open": 150.0, "high": 151.0, ...},
                    ...
                ]
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # Download historical data
            if start or end:
                df = ticker.history(
                    start=start,
                    end=end,
                    interval=interval,
                    auto_adjust=adjusted,
                    actions=True  # Include dividends and splits
                )
            else:
                df = ticker.history(
                    period=period,
                    interval=interval,
                    auto_adjust=adjusted,
                    actions=True
                )
            
            if df.empty:
                raise ValueError(f"No historical data for {symbol}")
            
            # Convert DataFrame to list of dicts
            result = []
            for date, row in df.iterrows():
                result.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "timestamp": date.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "adjusted_close": float(row["Close"]),  # Already adjusted if auto_adjust=True
                    "volume": int(row["Volume"]),
                    "dividend": float(row.get("Dividends", 0)),
                    "split": float(row.get("Stock Splits", 1)),
                })
            
            return {
                "symbol": symbol.upper(),
                "period": period,
                "interval": interval,
                "data": result
            }
        
        except Exception as e:
            logger.error(f"Yahoo Finance historical error for {symbol}: {e}")
            raise ValueError(f"Failed to get historical data for {symbol}: {e}")
    
    def get_intraday(
        self,
        symbol: str,
        interval: str = "5m",  # 1m, 2m, 5m, 15m, 30m, 60m, 90m
        period: str = "1d"     # 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
    ) -> Dict[str, Any]:
        """Get intraday prices.
        
        Args:
            symbol: Stock ticker
            interval: Time interval (1m, 2m, 5m, 15m, 30m, 60m, 90m)
            period: Data period (1d, 5d, 1mo, etc.)
        
        Returns:
            Dict with intraday time-series data
        
        Note:
            - 1m data only available for last 7 days
            - 2m data only available for last 60 days
            - 5m, 15m, 30m, 60m available for longer periods
        """
        try:
            ticker = yf.Ticker(symbol)
            
            df = ticker.history(
                period=period,
                interval=interval,
                actions=False
            )
            
            if df.empty:
                raise ValueError(f"No intraday data for {symbol}")
            
            result = []
            for timestamp, row in df.iterrows():
                result.append({
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                })
            
            return {
                "symbol": symbol.upper(),
                "interval": interval,
                "period": period,
                "data": result
            }
        
        except Exception as e:
            logger.error(f"Yahoo Finance intraday error for {symbol}: {e}")
            raise ValueError(f"Failed to get intraday data for {symbol}: {e}")
    
    def get_dividends(self, symbol: str) -> Dict[str, Any]:
        """Get dividend history for a symbol.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Dict with dividend data: {
                "symbol": "AAPL",
                "dividends": [
                    {"date": "2025-01-16", "amount": 0.25},
                    ...
                ]
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            dividends = ticker.dividends
            
            if dividends.empty:
                return {"symbol": symbol.upper(), "dividends": []}
            
            result = [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "amount": float(amount)
                }
                for date, amount in dividends.items()
            ]
            
            return {
                "symbol": symbol.upper(),
                "dividends": result
            }
        
        except Exception as e:
            logger.error(f"Yahoo Finance dividends error for {symbol}: {e}")
            raise ValueError(f"Failed to get dividends for {symbol}: {e}")
    
    def get_splits(self, symbol: str) -> Dict[str, Any]:
        """Get stock split history for a symbol.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Dict with split data: {
                "symbol": "AAPL",
                "splits": [
                    {"date": "2020-08-31", "ratio": 4.0},
                    ...
                ]
            }
        """
        try:
            ticker = yf.Ticker(symbol)
            splits = ticker.splits
            
            if splits.empty:
                return {"symbol": symbol.upper(), "splits": []}
            
            result = [
                {
                    "date": date.strftime("%Y-%m-%d"),
                    "ratio": float(ratio)
                }
                for date, ratio in splits.items()
            ]
            
            return {
                "symbol": symbol.upper(),
                "splits": result
            }
        
        except Exception as e:
            logger.error(f"Yahoo Finance splits error for {symbol}: {e}")
            raise ValueError(f"Failed to get splits for {symbol}: {e}")
    
    def get_info(self, symbol: str) -> Dict[str, Any]:
        """Get company information.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Dict with company info (sector, industry, market cap, etc.)
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol.upper(),
                "name": info.get("longName", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "country": info.get("country", ""),
                "website": info.get("website", ""),
                "description": info.get("longBusinessSummary", ""),
                "market_cap": info.get("marketCap", 0),
                "employees": info.get("fullTimeEmployees", 0),
                "exchange": info.get("exchange", ""),
                "currency": info.get("currency", "USD"),
            }
        
        except Exception as e:
            logger.error(f"Yahoo Finance info error for {symbol}: {e}")
            raise ValueError(f"Failed to get info for {symbol}: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass
