"""Data Infrastructure Integration Guide

This guide shows how to use the new data infrastructure (PostgreSQL, TimescaleDB, Redis, 
Alpha Vantage, Yahoo Finance) in your QuantLib Pro modules.

Sprint 1-2: Data Infrastructure Foundation - COMPLETION STATUS
============================================================

✅ COMPLETED TASKS (7/8):
1. ✅ Docker Compose updated with PostgreSQL, TimescaleDB, Redis, Celery, Dask
2. ✅ SQLAlchemy models created (Users, Portfolios, Holdings, Audit, Backtest, Celery, TimeSeries)
3. ✅ Alembic migrations configured (initial schema + hypertables)
4. ✅ Alpha Vantage client built (circuit breaker, rate limiting, retry)
5. ✅ Yahoo Finance client built (unlimited free tier)
6. ✅ Data provider router created (automatic fallback)
7. ✅ Redis cache layer enhanced (TTL management, statistics)

🔄 IN PROGRESS (Task 8):
8. Replace mocked data in modules (portfolio, risk, options, vol, regime)

================================================================================

QUICK START
===========

1. Start Infrastructure
-----------------------
```bash
# Start Docker services
cd "c:\\Users\\Administrator\\Downloads\\advanced quant"
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations
python scripts/migrate.py upgrade        # PostgreSQL tables
python scripts/migrate.py timescale      # TimescaleDB hypertables
```

2. Set Environment Variables
-----------------------------
Add to .env file:
```
# Alpha Vantage (optional, falls back to Yahoo Finance)
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Database URLs (auto-configured in Docker)
DATABASE_URL=postgresql://quantlib:changeme@postgres:5432/quantlib_db
TIMESCALE_URL=postgresql://quantlib:changeme@timescaledb:5433/timeseries_db
REDIS_URL=redis://redis:6379/0
```

3. Basic Usage Example
----------------------
```python
from quantlib_pro.data import (
    get_postgres_session,
    get_timescale_session,
    User,
    Portfolio,
    Price,
)
from quantlib_pro.data.data_router import DataProviderRouter
from quantlib_pro.data.cache_manager import CacheManager

# Initialize clients
data_router = DataProviderRouter()  # Auto-configures Alpha Vantage + Yahoo
cache = CacheManager()              # Redis caching

# Example 1: Get real-time quote (with auto-fallback and caching)
symbol = "AAPL"

# Try cache first
quote = cache.get("quote", symbol)
if not quote:
    # Fetch from API (tries Alpha Vantage, falls back to Yahoo)
    quote = data_router.get_quote(symbol)
    cache.set("quote", quote, symbol)  # Cache for 60s

print(f"{symbol}: ${quote['price']} ({quote['_provider']})")

# Example 2: Get historical data
historical = cache.get("historical", symbol, "1y")
if not historical:
    historical = data_router.get_historical(symbol, period="1y")
    cache.set("historical", historical, symbol, "1y")  # Cache for 24h

print(f"Fetched {len(historical['data'])} days of data")

# Example 3: Store data in databases
with get_postgres_session() as session:
    # Create user
    user = User(
        username="trader123",
        email="trader@example.com",
        password_hash="hashed_password",
        tier="pro"
    )
    session.add(user)
    session.commit()
    
    # Create portfolio
    portfolio = Portfolio(
        user_id=user.id,
        name="Growth Portfolio",
        initial_capital=100000
    )
    session.add(portfolio)
    session.commit()

with get_timescale_session() as session:
    # Store price data (TimescaleDB hypertable)
    for day in historical['data']:
        price = Price(
            time=day['date'],
            ticker=symbol,
            open=day['open'],
            high=day['high'],
            low=day['low'],
            close=day['close'],
            volume=day['volume'],
            adjusted_close=day['adjusted_close']
        )
        session.add(price)
    session.commit()

print("✓ Data stored in PostgreSQL and TimescaleDB")
```

================================================================================

HOW TO REPLACE MOCKED DATA
===========================

BEFORE (Old mocked code):
-------------------------
```python
# quantlib_pro/portfolio/metrics.py
import numpy as np

def get_portfolio_returns(tickers: list[str], days: int = 252) -> pd.DataFrame:
    # ❌ OLD: Mocked random data
    returns = {}
    for ticker in tickers:
        returns[ticker] = np.random.randn(days) * 0.02
    return pd.DataFrame(returns)
```

AFTER (New real data code):
---------------------------
```python
# quantlib_pro/portfolio/metrics.py
import pandas as pd
from quantlib_pro.data.data_router import DataProviderRouter
from quantlib_pro.data.cache_manager import CacheManager

def get_portfolio_returns(tickers: list[str], days: int = 252) -> pd.DataFrame:
    # ✅ NEW: Fetch real historical data with caching
    data_router = DataProviderRouter()
    cache = CacheManager()
    
    returns = {}
    for ticker in tickers:
        # Try cache first
        historical = cache.get("historical", ticker, "1y")
        if not historical:
            historical = data_router.get_historical(ticker, period="1y")
            cache.set("historical", historical, ticker, "1y")
        
        # Convert to returns
        df = pd.DataFrame(historical['data'])
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        returns[ticker] = df['close'].pct_change().dropna()
    
    return pd.DataFrame(returns).tail(days)
```

================================================================================

MODULE-SPECIFIC MIGRATION GUIDES
=================================

1. Portfolio Module (quantlib_pro/portfolio/)
----------------------------------------------
Files to update:
- metrics.py: Replace mocked returns with real data
- optimizer.py: Use real historical data for optimization
- analytics.py: Fetch real portfolio holdings from database

Example:
```python
# metrics.py - get_sharpe_ratio()
def get_sharpe_ratio(portfolio_id: str, days: int = 252) -> float:
    from quantlib_pro.data import get_postgres_session, get_timescale_session
    from quantlib_pro.data.models import Portfolio, Holding, Price
    
    with get_postgres_session() as psql:
        portfolio = psql.query(Portfolio).filter_by(id=portfolio_id).first()
        holdings = psql.query(Holding).filter_by(portfolio_id=portfolio_id).all()
    
    with get_timescale_session() as tsdb:
        # Get price data for all holdings
        tickers = [h.ticker for h in holdings]
        # ... fetch prices and calculate Sharpe ratio
```

2. Risk Module (quantlib_pro/risk/)
------------------------------------
Files to update:
- var.py: Use real returns for VaR calculation
- correlation.py: Calculate correlations from real data
- stress_test.py: Apply historical stress scenarios

Example:
```python
# var.py - calculate_var()
def calculate_var(
    tickers: list[str],
    confidence: float = 0.95,
    horizon: int = 1
) -> float:
    data_router = DataProviderRouter()
    cache = CacheManager()
    
    # Get real returns
    returns_data = {}
    for ticker in tickers:
        historical = data_router.get_historical(ticker, period="1y")
        df = pd.DataFrame(historical['data'])
        returns_data[ticker] = df['close'].pct_change().dropna()
    
    returns = pd.DataFrame(returns_data)
    # Calculate VaR from real returns...
```

3. Options Module (quantlib_pro/options/)
------------------------------------------
Files to update:
- pricing.py: Use real spot prices and volatility
- greeks.py: Calculate Greeks from real market data
- volatility_surface.py: Build vol surface from real option prices

Example:
```python
# pricing.py - black_scholes()
def black_scholes(
    ticker: str,
    strike: float,
    expiry_days: int,
    risk_free_rate: float = 0.05
) -> dict:
    data_router = DataProviderRouter()
    
    # Get real spot price
    quote = data_router.get_quote(ticker)
    spot = quote['price']
    
    # Get real volatility (from historical data)
    historical = data_router.get_historical(ticker, period="3mo")
    df = pd.DataFrame(historical['data'])
    returns = df['close'].pct_change().dropna()
    vol = returns.std() * np.sqrt(252)  # Annualized volatility
    
    # Calculate option price with real inputs...
```

4. Volatility Module (quantlib_pro/vol/)
-----------------------------------------
Files to update:
- surface.py: Build surface from real option prices
- smile.py: Calculate smile from real market data
- forecasting.py: Use real historical vol for forecasting

5. Market Regime Module (quantlib_pro/regime/)
-----------------------------------------------
Files to update:
- detector.py: Detect regimes from real market data
- hmm.py: Train HMM on real returns
- transitions.py: Calculate transition probabilities from real data

================================================================================

TESTING YOUR CHANGES
====================

1. Unit Tests
-------------
Create tests for your new data-fetching code:

```python
# tests/test_data_integration.py
import pytest
from quantlib_pro.data.data_router import DataProviderRouter

def test_fetch_real_quote():
    router = DataProviderRouter()
    quote = router.get_quote("AAPL")
    
    assert quote['symbol'] == 'AAPL'
    assert quote['price'] > 0
    assert '_provider' in quote  # Alpha Vantage or Yahoo Finance

def test_fetch_real_historical():
    router = DataProviderRouter()
    historical = router.get_historical("AAPL", period="1mo")
    
    assert historical['symbol'] == 'AAPL'
    assert len(historical['data']) >= 20  # At least 20 trading days
```

2. Integration Tests
--------------------
Test full workflow with database:

```python
# tests/test_database_integration.py
from quantlib_pro.data import get_postgres_session, User, Portfolio

def test_create_portfolio_with_real_user():
    with get_postgres_session() as session:
        # Create test user
        user = User(
            username="test_user",
            email="test@example.com",
            password_hash="test_hash",
            tier="free"
        )
        session.add(user)
        session.commit()
        
        # Create portfolio
        portfolio = Portfolio(
            user_id=user.id,
            name="Test Portfolio",
            initial_capital=10000
        )
        session.add(portfolio)
        session.commit()
        
        # Verify
        assert portfolio.id is not None
        assert portfolio.user_id == user.id
        
        # Cleanup
        session.delete(portfolio)
        session.delete(user)
        session.commit()
```

3. Run Tests
------------
```bash
pytest tests/ -v                        # All tests
pytest tests/test_data_integration.py   # Data tests only
pytest tests/test_portfolio.py          # Portfolio module
```

================================================================================

PERFORMANCE BEST PRACTICES
===========================

1. Always use caching for repeated queries:
   ✅ cache = CacheManager()
   ✅ data = cache.get("quote", symbol) or data_router.get_quote(symbol)

2. Batch fetch multiple symbols:
   ✅ quotes = data_router.get_batch_quotes(["AAPL", "MSFT", "GOOGL"])

3. Use database sessions correctly:
   ✅ with get_postgres_session() as session:
          # Do work
          session.commit()
   ❌ session = get_postgres_session_sync()  # Manual management

4. Cache warming for frequently accessed data:
   ✅ cache.warm_cache(["AAPL", "MSFT"], data_router)

5. Monitor cache hit rates:
   stats = cache.get_stats()
   print(f"Cache hit rate: {stats['hit_rate']:.2%}")

================================================================================

NEXT STEPS
==========

1. Replace mocked data in remaining modules:
   - quantlib_pro/portfolio/*.py (8 hours estimated)
   - quantlib_pro/risk/*.py (8 hours estimated)
   - quantlib_pro/options/*.py (6 hours estimated)

2. Create data population scripts:
   - scripts/populate_historical_data.py (backfill 10 years)
   - scripts/populate_user_data.py (sample users and portfolios)

3. Add data quality validation:
   - Check for missing/stale data
   - Validate data ranges
   - Monitor provider health

4. Create FastAPI endpoints:
   - /api/quote/{symbol}
   - /api/historical/{symbol}
   - /api/portfolio/{portfolio_id}

5. Add observability:
   - Prometheus metrics (cache hit rate, API latency)
   - Grafana dashboards
   - OpenTelemetry tracing

================================================================================

TROUBLESHOOTING
===============

Issue: "Alpha Vantage rate limit exceeded"
Solution: The router automatically falls back to Yahoo Finance. Check:
   provider_status = data_router.get_provider_status()
   # Wait 60s for circuit breaker to reset, or use Yahoo only

Issue: "Redis connection failed"
Solution: Caching is non-critical. Check Redis is running:
   docker-compose ps redis
   # System works without cache, just slower

Issue: "Database connection error"
Solution: Ensure databases are running:
   docker-compose -f docker-compose.prod.yml up -d postgres timescaledb
   python scripts/migrate.py upgrade

Issue: "Alembic migration failed"
Solution: Check DATABASE_URL environment variable and PostgreSQL is accessible

================================================================================

CONTACT & SUPPORT
=================

For questions or issues with the data infrastructure:
1. Check logs: docker-compose logs -f postgres redis
2. Review error messages (circuit breaker status, rate limits, etc.)
3. Test individual components (Alpha Vantage, Yahoo, Redis, PostgreSQL)

================================================================================
End of Integration Guide
"""