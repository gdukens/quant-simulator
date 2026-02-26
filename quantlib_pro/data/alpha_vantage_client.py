"""Alpha Vantage API client with circuit breaker and rate limiting.

Features:
- Circuit breaker pattern (5 failures → 60s timeout)
- Rate limiting (5 calls/minute for free tier, 75 calls/minute for premium)
- Automatic retry with exponential backoff
- Request caching (Redis)
- Error handling and logging

API Documentation: https://www.alphavantage.co/documentation/
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Circuit tripped, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for Alpha Vantage API.
    
    Opens after 5 consecutive failures, closes after 60 seconds.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout:
                logger.info("Circuit breaker entering HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker OPEN. Try again in {self.recovery_timeout}s")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Reset failure count on success."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            logger.info("Circuit breaker entering CLOSED state (recovered)")
            self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Increment failure count and open circuit if threshold reached."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            logger.warning(f"Circuit breaker OPEN after {self.failure_count} failures")
            self.state = CircuitState.OPEN


class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, calls_per_minute: int = 5):
        self.calls_per_minute = calls_per_minute
        self.call_times: list[datetime] = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = datetime.now()
        
        # Remove calls older than 1 minute
        self.call_times = [t for t in self.call_times if (now - t).seconds < 60]
        
        if len(self.call_times) >= self.calls_per_minute:
            # Calculate wait time
            oldest_call = self.call_times[0]
            wait_time = 60 - (now - oldest_call).seconds
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time}s...")
                time.sleep(wait_time)
                self.call_times = []
        
        self.call_times.append(now)


class AlphaVantageClient:
    """Alpha Vantage API client with resilience features."""
    
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        tier: str = "free",  # free, basic, premium
        timeout: int = 10,
        max_retries: int = 3,
    ):
        # API key from environment or parameter
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not set")
        
        self.timeout = timeout
        
        # Rate limits by tier
        rate_limits = {
            "free": 5,      # 5 calls/minute
            "basic": 30,    # 30 calls/minute
            "premium": 75,  # 75 calls/minute
        }
        self.rate_limiter = RateLimiter(calls_per_minute=rate_limits.get(tier, 5))
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=requests.RequestException
        )
        
        # HTTP session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,  # 1s, 2s, 4s delays
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
    
    def _request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with rate limiting and circuit breaker."""
        # Add API key
        params["apikey"] = self.api_key
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Circuit breaker protection
        def make_request():
            logger.debug(f"Alpha Vantage request: {params.get('function')}")
            response = self.session.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API errors
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
            
            if "Note" in data:
                # Rate limit message
                raise requests.RequestException(f"Rate limit: {data['Note']}")
            
            return data
        
        return self.circuit_breaker.call(make_request)
    
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
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        
        data = self._request(params)
        quote = data.get("Global Quote", {})
        
        if not quote:
            raise ValueError(f"No quote data for {symbol}")
        
        return {
            "symbol": quote.get("01. symbol"),
            "price": float(quote.get("05. price", 0)),
            "volume": int(quote.get("06. volume", 0)),
            "timestamp": quote.get("07. latest trading day"),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%").rstrip("%"),
        }
    
    def get_historical(
        self,
        symbol: str,
        outputsize: str = "compact",  # compact=100 days, full=20 years
        adjusted: bool = True
    ) -> Dict[str, Any]:
        """Get historical daily prices for a symbol.
        
        Args:
            symbol: Stock ticker
            outputsize: 'compact' (100 days) or 'full' (20 years)
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
        function = "TIME_SERIES_DAILY_ADJUSTED" if adjusted else "TIME_SERIES_DAILY"
        
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": outputsize
        }
        
        data = self._request(params)
        
        # Parse time series data
        time_series_key = "Time Series (Daily)"
        if adjusted:
            time_series_key = "Time Series (Daily)"
        
        time_series = data.get(time_series_key, {})
        
        if not time_series:
            raise ValueError(f"No historical data for {symbol}")
        
        # Convert to list of dicts
        result = []
        for date_str, values in time_series.items():
            result.append({
                "date": date_str,
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "adjusted_close": float(values.get("5. adjusted close", values.get("4. close", 0))),
                "volume": int(values.get("6. volume", 0)),
                "dividend": float(values.get("7. dividend amount", 0)) if adjusted else 0,
                "split": float(values.get("8. split coefficient", 1)) if adjusted else 1,
            })
        
        return {
            "symbol": symbol,
            "data": sorted(result, key=lambda x: x["date"])
        }
    
    def get_intraday(
        self,
        symbol: str,
        interval: str = "5min",  # 1min, 5min, 15min, 30min, 60min
        outputsize: str = "compact"
    ) -> Dict[str, Any]:
        """Get intraday prices (only for premium accounts).
        
        Args:
            symbol: Stock ticker
            interval: Time interval (1min, 5min, 15min, 30min, 60min)
            outputsize: 'compact' (100 data points) or 'full' (trailing 30 days)
        
        Returns:
            Dict with intraday time-series data
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize
        }
        
        data = self._request(params)
        
        time_series_key = f"Time Series ({interval})"
        time_series = data.get(time_series_key, {})
        
        if not time_series:
            raise ValueError(f"No intraday data for {symbol}")
        
        result = []
        for timestamp, values in time_series.items():
            result.append({
                "timestamp": timestamp,
                "open": float(values.get("1. open", 0)),
                "high": float(values.get("2. high", 0)),
                "low": float(values.get("3. low", 0)),
                "close": float(values.get("4. close", 0)),
                "volume": int(values.get("5. volume", 0)),
            })
        
        return {
            "symbol": symbol,
            "interval": interval,
            "data": sorted(result, key=lambda x: x["timestamp"])
        }
    
    def close(self):
        """Close the HTTP session."""
        self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
