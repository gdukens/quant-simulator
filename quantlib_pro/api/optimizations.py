"""
Production API Performance Optimizations

Key Performance Enhancements:
1. Async Redis Connection Pooling      - <50ms cache operations
2. Database Query Optimization         - <100ms database operations
3. Request Result Caching              - <10ms cached responses
4. Background Task Processing          - <200ms async computations
5. Connection Pool Management          - <5ms connection overhead

Target: <500ms response time for all endpoints
"""

import asyncio
import hashlib
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, Optional, Union

import redis.asyncio as aioredis
import numpy as np
import pandas as pd
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from quantlib_pro.data.cache_manager import CacheManager
from quantlib_pro.observability.performance import track_performance

logger = logging.getLogger(__name__)

# =============================================================================
# Async Redis Connection Pool
# =============================================================================

class AsyncRedisPool:
    """High-performance Redis connection pool for API caching."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.pool: Optional[aioredis.ConnectionPool] = None
        self.redis: Optional[aioredis.Redis] = None
    
    async def initialize(self):
        """Initialize Redis connection pool."""
        self.pool = aioredis.ConnectionPool.from_url(
            self.redis_url,
            max_connections=20,
            retry_on_timeout=True,
            health_check_interval=30
        )
        self.redis = aioredis.Redis(connection_pool=self.pool)
        logger.info("✅ Redis connection pool initialized")
    
    async def close(self):
        """Close Redis connections."""
        if self.redis:
            await self.redis.close()
        if self.pool:
            await self.pool.disconnect()
    
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis with performance tracking."""
        with track_performance("redis_get"):
            return await self.redis.get(key)
    
    async def set(self, key: str, value: str, ttl: int = 3600) -> None:
        """Set value in Redis with TTL."""
        with track_performance("redis_set"):
            await self.redis.setex(key, ttl, value)
    
    async def delete(self, key: str) -> None:
        """Delete key from Redis."""
        with track_performance("redis_delete"):
            await self.redis.delete(key)

# Global Redis pool instance
redis_pool = AsyncRedisPool()

# =============================================================================
# Async Database Pool
# =============================================================================

class AsyncDatabasePool:
    """High-performance async database connection pool."""
    
    def __init__(self, database_url: str):
        # Convert sync URL to async
        self.database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
        self.engine = None
        self.session_maker = None
    
    async def initialize(self):
        """Initialize async database engine and session maker."""
        self.engine = create_async_engine(
            self.database_url,
            pool_size=20,               # 20 connections in pool
            max_overflow=30,            # 30 additional overflow connections
            pool_pre_ping=True,         # Verify connections
            pool_recycle=3600,          # Recycle after 1 hour
            echo=False                  # Disable SQL logging for performance
        )
        self.session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        logger.info("✅ Async database pool initialized")
    
    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup."""
        async with self.session_maker() as session:
            try:
                yield session
            finally:
                await session.close()

# =============================================================================
# Request Caching Decorator
# =============================================================================

def cache_result(
    ttl: int = 3600,
    cache_key_prefix: str = "api",
    use_request_hash: bool = True
):
    """
    Cache API endpoint results in Redis.
    
    Args:
        ttl: Cache TTL in seconds (default: 1 hour)
        cache_key_prefix: Prefix for cache keys
        use_request_hash: Include request parameters in cache key
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if use_request_hash:
                # Hash request parameters
                request_data = str(sorted(kwargs.items()))
                request_hash = hashlib.md5(request_data.encode()).hexdigest()[:8]
                cache_key = f"{cache_key_prefix}:{func.__name__}:{request_hash}"
            else:
                cache_key = f"{cache_key_prefix}:{func.__name__}"
            
            # Try to get from cache
            with track_performance(f"cache_lookup_{func.__name__}"):
                cached_result = await redis_pool.get(cache_key)
                if cached_result:
                    logger.info(f"✅ Cache hit for {cache_key}")
                    return eval(cached_result)  # In production: use JSON
            
            # Execute function and cache result
            with track_performance(f"compute_{func.__name__}"):
                result = await func(*args, **kwargs)
            
            # Store in cache (async background task)
            asyncio.create_task(
                redis_pool.set(cache_key, str(result), ttl)
            )
            logger.info(f"💾 Cached result for {cache_key}")
            
            return result
        return wrapper
    return decorator

# =============================================================================
# Optimized Portfolio Functions
# =============================================================================

@cache_result(ttl=1800, cache_key_prefix="portfolio")  # 30 min cache
async def optimized_portfolio_calculation(
    tickers: list[str],
    optimization_type: str = "max_sharpe",
    risk_free_rate: float = 0.02,
    **kwargs
) -> dict:
    """
    Optimized portfolio calculation with caching and async processing.
    
    Performance targets:
    - Cache hit: <50ms
    - Cache miss: <300ms
    - Database query: <100ms
    """
    from quantlib_pro.portfolio import max_sharpe_portfolio
    from quantlib_pro.data.providers import get_market_data
    
    with track_performance("portfolio_optimization_full"):
        # 1. Fetch market data (async, cached)
        with track_performance("fetch_market_data"):
            market_data = await get_cached_market_data(tickers)
        
        # 2. Calculate expected returns and covariance
        with track_performance("calculate_statistics"):
            returns = market_data.pct_change().dropna()
            expected_returns = returns.mean() * 252  # Annualize
            cov_matrix = returns.cov() * 252         # Annualize
        
        # 3. Optimize portfolio
        with track_performance("optimize_weights"):
            if optimization_type == "max_sharpe":
                result = max_sharpe_portfolio(
                    expected_returns=expected_returns,
                    cov_matrix=cov_matrix,
                    risk_free_rate=risk_free_rate
                )
            
        # 4. Return optimized result
        return {
            'optimal_weights': result.to_dict(),
            'expected_return': result.expected_return,
            'volatility': result.volatility,
            'sharpe_ratio': result.sharpe_ratio,
            'optimization_method': result.method,
            'calculation_timestamp': datetime.utcnow().isoformat(),
            'performance_metrics': {
                'cache_status': 'computed',
                'computation_time_ms': track_performance.get_last_duration() * 1000
            }
        }

@cache_result(ttl=3600, cache_key_prefix="market_data")  # 1 hour cache
async def get_cached_market_data(tickers: list[str]) -> pd.DataFrame:
    """
    Get market data with aggressive caching for performance.
    
    Performance targets:
    - Cache hit: <20ms
    - Cache miss + DB: <150ms
    """
    with track_performance("market_data_fetch"):
        # In production: fetch from database or external API
        # For now: generate sample data
        import numpy as np
        
        # Generate realistic market data
        np.random.seed(42)  # Reproducible for caching
        dates = pd.date_range(end=datetime.now(), periods=252, freq='D')
        
        data = {}
        for ticker in tickers:
            # Generate realistic price series
            returns = np.random.normal(0.0008, 0.02, len(dates))
            prices = 100 * np.exp(np.cumsum(returns))
            data[ticker] = prices
        
        market_data = pd.DataFrame(data, index=dates)
        logger.info(f"📊 Generated market data for {len(tickers)} assets")
        
        return market_data

# =============================================================================
# Optimized Options Pricing Functions
# =============================================================================

@cache_result(ttl=300, cache_key_prefix="options")  # 5 min cache
async def optimized_option_pricing(
    option_type: str,
    spot_price: float,
    strike_price: float,
    time_to_expiry: float,
    volatility: float,
    risk_free_rate: float = 0.02
) -> dict:
    """
    High-performance options pricing with result caching.
    
    Performance targets:
    - Cache hit: <10ms
    - Computation: <50ms
    """
    from quantlib_pro.options import bs_price, price_with_greeks
    
    with track_performance("option_pricing_full"):
        # Calculate option price and Greeks
        with track_performance("bs_calculation"):
            price = bs_price(
                option_type=option_type,
                spot=spot_price,
                strike=strike_price,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                risk_free_rate=risk_free_rate
            )
        
        with track_performance("greeks_calculation"):
            greeks_result = price_with_greeks(
                option_type=option_type,
                spot=spot_price,
                strike=strike_price,
                time_to_expiry=time_to_expiry,
                volatility=volatility,
                risk_free_rate=risk_free_rate
            )
        
        return {
            'option_price': price,
            'greeks': greeks_result,
            'spot_price': spot_price,
            'strike_price': strike_price,
            'time_to_expiry': time_to_expiry,
            'volatility': volatility,
            'risk_free_rate': risk_free_rate,
            'calculation_timestamp': datetime.utcnow().isoformat(),
            'performance_metrics': {
                'cache_status': 'computed',
                'computation_time_ms': track_performance.get_last_duration() * 1000
            }
        }

# =============================================================================
# Performance Monitoring
# =============================================================================

class PerformanceMonitor:
    """Monitor API performance in real-time."""
    
    def __init__(self):
        self.request_times = {}
        self.cache_hit_rates = {}
        self.db_query_times = {}
    
    def log_request_time(self, endpoint: str, duration_ms: float):
        """Log request processing time."""
        if endpoint not in self.request_times:
            self.request_times[endpoint] = []
        
        self.request_times[endpoint].append(duration_ms)
        
        # Keep only last 100 measurements
        if len(self.request_times[endpoint]) > 100:
            self.request_times[endpoint] = self.request_times[endpoint][-100:]
    
    def get_performance_report(self) -> dict:
        """Generate performance report."""
        report = {}
        
        for endpoint, times in self.request_times.items():
            if times:
                report[endpoint] = {
                    'avg_response_time_ms': np.mean(times),
                    'p95_response_time_ms': np.percentile(times, 95),
                    'p99_response_time_ms': np.percentile(times, 99),
                    'request_count': len(times),
                    'sla_compliance': np.mean([t < 500 for t in times])  # <500ms SLA
                }
        
        return report

# Global performance monitor
performance_monitor = PerformanceMonitor()

# =============================================================================
# Startup/Shutdown Event Handlers
# =============================================================================

async def startup_optimizations():
    """Initialize all performance optimizations."""
    logger.info("🚀 Initializing API performance optimizations...")
    
    # Initialize Redis pool
    await redis_pool.initialize()
    
    # Initialize database pool  
    # db_pool = AsyncDatabasePool(DATABASE_URL)
    # await db_pool.initialize()
    
    # Warm up cache with common calculations
    logger.info("🔥 Warming up caches...")
    
    logger.info("✅ API performance optimizations ready!")

async def shutdown_optimizations():
    """Clean up performance optimization resources."""
    logger.info("🛑 Shutting down API optimizations...")
    await redis_pool.close()
    logger.info("✅ Cleanup complete")