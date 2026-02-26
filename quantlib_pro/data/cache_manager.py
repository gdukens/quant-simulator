"""Enhanced Redis cache manager for market data.

Features:
- Automatic cache key generation
- TTL management by data type
- Cache invalidation strategies
- Cache warming
- Cache statistics
- Integration with data router

Cache Key Schema:
- quote:{symbol}                      → Real-time quote (TTL: 60s)
- historical:{symbol}:{period}        → Historical data (TTL: 24h)
- intraday:{symbol}:{interval}        → Intraday data (TTL: 5min)
- correlation_matrix:{symbols}:{days} → Correlation matrix (TTL: 1h)
- vol_surface:{symbol}                → Volatility surface (TTL: 1h)
"""

import os
import json
import logging
import hashlib
from typing import Any, Dict, Optional, List
from datetime import datetime, timedelta

import redis
import pandas as pd


logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for market data."""
    
    # Default TTLs by data type (in seconds)
    TTL_DEFAULTS = {
        "quote": 60,                # Real-time quotes: 1 minute
        "historical": 86400,        # Historical data: 24 hours
        "intraday": 300,            # Intraday data: 5 minutes
        "correlation_matrix": 3600, # Correlation: 1 hour
        "vol_surface": 3600,        # Volatility surface: 1 hour
        "portfolio": 300,           # Portfolio data: 5 minutes
        "backtest": 7200,           # Backtest results: 2 hours
        "regime_state": 1800,       # Regime state: 30 minutes
    }
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        key_prefix: str = "quantlib:",
        enabled: bool = True
    ):
        """Initialize cache manager.
        
        Args:
            redis_url: Redis connection URL (default: from REDIS_URL env)
            key_prefix: Prefix for all cache keys
            enabled: Enable/disable caching (useful for testing)
        """
        self.key_prefix = key_prefix
        self.enabled = enabled
        
        # Initialize Redis connection
        self.redis_client: Optional[redis.Redis] = None
        
        if enabled:
            try:
                redis_url = redis_url or os.getenv(
                    "REDIS_URL",
                    "redis://localhost:6379/0"
                )
                self.redis_client = redis.from_url(
                    redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                    max_connections=20
                )
                # Test connection
                self.redis_client.ping()
                logger.info(f"✓ Redis cache connected: {redis_url}")
            except Exception as e:
                logger.warning(f"Redis cache unavailable: {e}. Caching disabled.")
                self.redis_client = None
                self.enabled = False
    
    def _build_key(self, data_type: str, *args) -> str:
        """Build cache key from data type and arguments.
        
        Args:
            data_type: Type of data (quote, historical, etc.)
            *args: Arguments to include in key (symbol, period, etc.)
        
        Returns:
            Cache key: "quantlib:quote:AAPL"
        """
        parts = [data_type] + [str(arg) for arg in args]
        key = ":".join(parts)
        return f"{self.key_prefix}{key}"
    
    def _hash_key(self, data: str) -> str:
        """Generate hash for data (for complex keys)."""
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def get(self, data_type: str, *args) -> Optional[Any]:
        """Get data from cache.
        
        Args:
            data_type: Type of data
            *args: Key components
        
        Returns:
            Cached data or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        key = self._build_key(data_type, *args)
        
        try:
            raw_data = self.redis_client.get(key)
            if raw_data is None:
                logger.debug(f"Cache MISS: {key}")
                return None
            
            # Parse JSON
            data = json.loads(raw_data)
            logger.debug(f"Cache HIT: {key}")
            return data
        
        except Exception as e:
            logger.warning(f"Cache GET error for {key}: {e}")
            return None
    
    def set(
        self,
        data_type: str,
        data: Any,
        *args,
        ttl: Optional[int] = None
    ) -> bool:
        """Set data in cache.
        
        Args:
            data_type: Type of data
            data: Data to cache (must be JSON-serializable)
            *args: Key components
            ttl: Time to live in seconds (default: from TTL_DEFAULTS)
        
        Returns:
            True if cached successfully
        """
        if not self.enabled or not self.redis_client:
            return False
        
        key = self._build_key(data_type, *args)
        ttl = ttl or self.TTL_DEFAULTS.get(data_type, 3600)
        
        try:
            # Serialize to JSON
            raw_data = json.dumps(data)
            
            # Set with TTL
            self.redis_client.setex(key, ttl, raw_data)
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True
        
        except Exception as e:
            logger.warning(f"Cache SET error for {key}: {e}")
            return False
    
    def get_dataframe(self, data_type: str, *args) -> Optional[pd.DataFrame]:
        """Get DataFrame from cache.
        
        Args:
            data_type: Type of data
            *args: Key components
        
        Returns:
            Cached DataFrame or None
        """
        data = self.get(data_type, *args)
        if data is None:
            return None
        
        try:
            return pd.DataFrame(data)
        except Exception as e:
            logger.warning(f"Failed to convert cached data to DataFrame: {e}")
            return None
    
    def set_dataframe(
        self,
        data_type: str,
        df: pd.DataFrame,
        *args,
        ttl: Optional[int] = None
    ) -> bool:
        """Set DataFrame in cache.
        
        Args:
            data_type: Type of data
            df: DataFrame to cache
            *args: Key components
            ttl: Time to live in seconds
        
        Returns:
            True if cached successfully
        """
        try:
            # Convert DataFrame to dict (records format for efficiency)
            data = df.to_dict('records') if not df.empty else []
            return self.set(data_type, data, *args, ttl=ttl)
        except Exception as e:
            logger.warning(f"Failed to cache DataFrame: {e}")
            return False
    
    def delete(self, data_type: str, *args) -> bool:
        """Delete data from cache.
        
        Args:
            data_type: Type of data
            *args: Key components
        
        Returns:
            True if deleted successfully
        """
        if not self.enabled or not self.redis_client:
            return False
        
        key = self._build_key(data_type, *args)
        
        try:
            self.redis_client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
            return True
        except Exception as e:
            logger.warning(f"Cache DELETE error for {key}: {e}")
            return False
    
    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern.
        
        Args:
            pattern: Redis pattern (e.g., "quote:*")
        
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        full_pattern = f"{self.key_prefix}{pattern}"
        
        try:
            keys = list(self.redis_client.scan_iter(match=full_pattern, count=100))
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} keys matching {full_pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Pattern invalidation error: {e}")
            return 0
    
    def invalidate_symbol(self, symbol: str) -> int:
        """Invalidate all cached data for a symbol.
        
        Args:
            symbol: Stock ticker
        
        Returns:
            Number of keys deleted
        """
        return self.invalidate_pattern(f"*:{symbol}*")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict with cache stats: {
                "connected": True,
                "keys": 1234,
                "memory_used": "10.5 MB",
                "hit_rate": 0.85
            }
        """
        if not self.enabled or not self.redis_client:
            return {"connected": False}
        
        try:
            info = self.redis_client.info()
            keyspace = self.redis_client.info("keyspace")
            
            # Extract stats
            db0 = keyspace.get("db0", {})
            keys = db0.get("keys", 0)
            
            return {
                "connected": True,
                "keys": keys,
                "memory_used": info.get("used_memory_human", "N/A"),
                "hit_rate": info.get("keyspace_hit_rate", 0),
                "uptime_seconds": info.get("uptime_in_seconds", 0),
                "connected_clients": info.get("connected_clients", 0),
            }
        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def flush_all(self) -> bool:
        """Flush all keys from cache (DANGEROUS - use only in dev/test).
        
        Returns:
            True if successful
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.warning("Cache flushed (all keys deleted)")
            return True
        except Exception as e:
            logger.error(f"Cache flush error: {e}")
            return False
    
    def warm_cache(self, symbols: List[str], data_router: Any):
        """Pre-populate cache with data for symbols.
        
        Args:
            symbols: List of stock tickers
            data_router: DataProviderRouter instance
        """
        logger.info(f"Warming cache for {len(symbols)} symbols...")
        
        for symbol in symbols:
            try:
                # Fetch and cache quote
                quote = data_router.get_quote(symbol)
                self.set("quote", quote, symbol)
                
                # Fetch and cache 1-year historical data
                historical = data_router.get_historical(symbol, period="1y")
                self.set("historical", historical, symbol, "1y")
                
                logger.debug(f"Warmed cache for {symbol}")
            except Exception as e:
                logger.warning(f"Failed to warm cache for {symbol}: {e}")
        
        logger.info(f"✓ Cache warming complete")
    
    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            self.redis_client.close()
            logger.info("Cache connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Global cache instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
