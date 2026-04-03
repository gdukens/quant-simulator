# QuantLib Pro Architecture

## Overview

QuantLib Pro is built using a **hexagonal (ports and adapters) architecture** with clear separation of concerns across domain logic, application services, and infrastructure.

## Design Principles

1. **Separation of Concerns**: Business logic isolated from infrastructure
2. **Dependency Inversion**: Dependencies point inward toward domain
3. **Single Responsibility**: Each module has one clear purpose
4. **Open/Closed**: Open for extension, closed for modification
5. **Interface Segregation**: Small, focused interfaces
6. **DRY (Don't Repeat Yourself)**: Reusable components

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Presentation Layer                      │
│                    (Streamlit UI Pages)                      │
├─────────────────────────────────────────────────────────────┤
│                    Application Services                      │
│              (Orchestration & Use Cases)                     │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│        (Business Logic, Models, Entities)                    │
├─────────────────────────────────────────────────────────────┤
│                  Infrastructure Layer                        │
│       (Data Providers, Persistence, External APIs)           │
└─────────────────────────────────────────────────────────────┘
```

---

## Layer Architecture

### 1. Presentation Layer

**Location:** `pages/`

Streamlit-based user interface with multiple specialized pages.

**Components:**
- `Home.py` - Landing page and overview
- `1__Portfolio_Optimizer.py` - Portfolio optimization UI
- `2__Risk_Analytics.py` - Risk analysis dashboard
- `3__Options_Pricing.py` - Derivatives pricing
- `4__Backtesting.py` - Strategy backtesting
- `5__Regime_Detection.py` - Market regime analysis
- `6__Monte_Carlo.py` - Monte Carlo simulations
- `7__Data_Explorer.py` - Data visualization
- `8__Advanced_Analytics.py` - Performance & stress testing
- `9__Testing.py` - Testing & validation dashboard

**Responsibilities:**
- User input validation
- Data visualization (Plotly charts)
- Session state management
- Error handling and user feedback

**Technology Stack:**
- Streamlit for web UI
- Plotly for interactive charts
- Pandas for data display

---

### 2. Application Services Layer

**Location:** `quantlib_pro/`

Orchestrates business logic and coordinates between layers.

**Modules:**

#### Portfolio Management (`portfolio/`)
- `optimizer.py` - Portfolio optimization algorithms
- `rebalancer.py` - Portfolio rebalancing logic
- `performance.py` - Performance attribution

#### Risk Analytics (`risk/`)
- `calculator.py` - VaR, CVaR calculations
- `advanced_analytics.py` - Stress testing, tail risk
- `metrics.py` - Risk metrics computation

#### Derivatives Pricing (`derivatives/`)
- `black_scholes.py` - Analytical pricing models
- `monte_carlo.py` - Monte Carlo pricing engine
- `greeks.py` - Options Greeks calculation

#### Data Management (`data/`)
- `providers.py` - Market data providers
- `validator.py` - Data quality checks
- `cache.py` - Data caching layer

#### Backtesting (`backtesting/`)
- `engine.py` - Backtesting engine
- `strategy.py` - Strategy base class
- `metrics.py` - Performance metrics

#### Analytics (`analytics/`)
- `regime_detection.py` - Market regime detection
- `correlation_analysis.py` - Correlation regime analysis
- `factor_models.py` - Factor analysis

---

### 3. Domain Layer

**Location:** Core business logic within each module

Pure business logic with no external dependencies.

**Components:**

#### Mathematical Models
- Modern Portfolio Theory (MPT)
- Black-Scholes-Merton model
- Monte Carlo simulation
- Time series analysis

#### Business Rules
- Investment constraints
- Risk limits
- Position sizing
- Rebalancing thresholds

#### Domain Entities
- Portfolio
- Security
- Trade
- Position
- RiskMetrics

**Characteristics:**
- No framework dependencies
- Highly testable
- Pure functions where possible
- Domain-driven design

---

### 4. Infrastructure Layer

**Location:** External integrations and persistence

**Components:**

#### Data Providers
```python
# Adapter pattern for multiple data sources
class DataProvider(ABC):
    @abstractmethod
    def get_historical_data(self, tickers, start, end):
        pass
    
    @abstractmethod
    def get_quote(self, ticker):
        pass

class YFinanceProvider(DataProvider):
    # Yahoo Finance implementation
    pass

class AlphaVantageProvider(DataProvider):
    # Alpha Vantage implementation
    pass
```

#### Persistence
- JSON for configuration
- CSV for data exports
- Pickle for model serialization

#### External APIs
- Market data APIs (yfinance, alpha_vantage)
- Database connections (optional)

---

## Module Organization

```
quantlib_pro/
├── portfolio/              # Portfolio management
│   ├── __init__.py
│   ├── optimizer.py
│   └── rebalancer.py
│
├── risk/                   # Risk analytics
│   ├── __init__.py
│   ├── calculator.py
│   └── advanced_analytics.py
│
├── derivatives/            # Options & derivatives
│   ├── __init__.py
│   ├── black_scholes.py
│   └── monte_carlo.py
│
├── data/                   # Data management
│   ├── __init__.py
│   ├── providers.py
│   └── validator.py
│
├── backtesting/            # Strategy backtesting
│   ├── __init__.py
│   ├── engine.py
│   └── strategy.py
│
├── analytics/              # Advanced analytics
│   ├── __init__.py
│   ├── regime_detection.py
│   └── correlation_analysis.py
│
├── governance/             # Compliance & audit
│   ├── __init__.py
│   ├── compliance.py
│   └── audit.py
│
├── observability/          # Monitoring & profiling
│   ├── __init__.py
│   ├── profiler.py
│   └── monitoring.py
│
└── testing/                # Testing infrastructure
    ├── __init__.py
    ├── load_testing.py
    ├── chaos.py
    ├── model_validation.py
    └── reporting.py
```

---

## Key Design Patterns

### 1. Strategy Pattern

Used for multiple algorithm implementations:

```python
class OptimizationStrategy(ABC):
    @abstractmethod
    def optimize(self, returns, cov_matrix):
        pass

class MaxSharpeStrategy(OptimizationStrategy):
    def optimize(self, returns, cov_matrix):
        # Implementation
        pass

class MinVolatilityStrategy(OptimizationStrategy):
    def optimize(self, returns, cov_matrix):
        # Implementation
        pass
```

### 2. Factory Pattern

For creating data providers:

```python
class DataProviderFactory:
    @staticmethod
    def create(source: str) -> DataProvider:
        if source == 'yfinance':
            return YFinanceProvider()
        elif source == 'alpha_vantage':
            return AlphaVantageProvider()
        else:
            raise ValueError(f"Unknown source: {source}")
```

### 3. Decorator Pattern

For profiling and monitoring:

```python
@profile
def expensive_calculation():
    # Automatically profiled
    pass

@monitor
def critical_operation():
    # Automatically monitored
    pass
```

### 4. Observer Pattern

For real-time monitoring:

```python
class PerformanceMonitor:
    def __init__(self):
        self.observers = []
    
    def attach(self, observer):
        self.observers.append(observer)
    
    def notify(self, event):
        for observer in self.observers:
            observer.update(event)
```

### 5. Builder Pattern

For complex object construction:

```python
class BacktestBuilder:
    def __init__(self):
        self._strategy = None
        self._data = None
        self._config = {}
    
    def with_strategy(self, strategy):
        self._strategy = strategy
        return self
    
    def with_data(self, data):
        self._data = data
        return self
    
    def with_config(self, **kwargs):
        self._config.update(kwargs)
        return self
    
    def build(self):
        return Backtester(self._strategy, self._data, self._config)
```

---

## Data Flow

### 1. Portfolio Optimization Flow

```
User Input (UI)
    ↓
Application Service (PortfolioOptimizer)
    ↓
Domain Logic (MPT calculations)
    ↓
Infrastructure (Data Provider)
    ↓
Persistence (Cache/Export)
    ↓
UI (Results Display)
```

### 2. Risk Calculation Flow

```
Portfolio Data
    ↓
Risk Calculator
    ↓
VaR/CVaR Computation
    ↓
Stress Testing (optional)
    ↓
Risk Metrics
    ↓
Reporting & Alerts
```

### 3. Backtesting Flow

```
Strategy Definition
    ↓
Historical Data
    ↓
Signal Generation
    ↓
Trade Execution Simulation
    ↓
Performance Metrics
    ↓
Results & Analytics
```

---

## Error Handling Strategy

### 1. Validation Layer

```python
def validate_portfolio_inputs(returns, cov_matrix):
    """Validate inputs before processing."""
    if returns.empty:
        raise ValueError("Returns cannot be empty")
    
    if not np.allclose(cov_matrix, cov_matrix.T):
        raise ValueError("Covariance matrix must be symmetric")
    
    if np.linalg.det(cov_matrix) <= 0:
        raise ValueError("Covariance matrix must be positive definite")
```

### 2. Error Recovery

```python
class DataProvider:
    def get_data_with_fallback(self, tickers):
        try:
            return self.primary_source.get_data(tickers)
        except Exception as e:
            logger.warning(f"Primary source failed: {e}")
            return self.fallback_source.get_data(tickers)
```

### 3. Graceful Degradation

```python
def calculate_var_with_fallback(returns):
    try:
        # Try Monte Carlo (most accurate)
        return monte_carlo_var(returns)
    except Exception:
        try:
            # Fallback to historical
            return historical_var(returns)
        except Exception:
            # Last resort: parametric
            return parametric_var(returns)
```

---

## Performance Optimization

### 1. Caching Strategy

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_covariance_matrix(returns_hash):
    """Cache expensive covariance calculations."""
    return returns.cov()
```

### 2. Vectorization

```python
# Instead of loops
returns_mean = []
for col in returns.columns:
    returns_mean.append(returns[col].mean())

# Use vectorized operations
returns_mean = returns.mean()  # Much faster
```

### 3. Lazy Loading

```python
class Portfolio:
    @property
    def efficient_frontier(self):
        if not hasattr(self, '_frontier'):
            self._frontier = self._calculate_frontier()
        return self._frontier
```

### 4. Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor

def parallel_var_calculation(portfolios):
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = executor.map(calculate_var, portfolios)
    return list(results)
```

---

## Testing Strategy

### 1. Unit Tests

Test individual components in isolation:

```python
def test_black_scholes_call():
    pricer = BlackScholesPricer(S=100, K=100, T=1, r=0.05, sigma=0.2)
    call_price = pricer.call_price()
    assert abs(call_price - 10.45) < 0.01  # Known value
```

### 2. Integration Tests

Test component interactions:

```python
def test_portfolio_to_risk_workflow():
    optimizer = PortfolioOptimizer(returns, cov_matrix)
    weights = optimizer.max_sharpe_ratio()
    
    calculator = RiskCalculator()
    var = calculator.calculate_var(returns, weights)
    
    assert var < 0  # VaR should be negative
```

### 3. Load Tests

Test performance under load:

```python
def test_concurrent_optimizations():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(optimizer.max_sharpe_ratio) 
                  for _ in range(10)]
        results = [f.result() for f in futures]
    
    assert all(r is not None for r in results)
```

### 4. Model Validation

Validate against known benchmarks:

```python
def test_option_pricing_accuracy():
    pricer = BlackScholesPricer(S=100, K=100, T=1, r=0.05, sigma=0.2)
    call = pricer.call_price()
    
    # Hull's Options book benchmark
    expected = 10.45
    assert abs(call - expected) / expected < 0.01  # <1% error
```

---

## Security Considerations

### 1. Input Validation

```python
def validate_ticker(ticker: str) -> bool:
    """Prevent SQL injection and invalid tickers."""
    return bool(re.match(r'^[A-Z]{1,5}$', ticker))
```

### 2. API Key Management

```python
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')  # Never hardcode
```

### 3. Data Sanitization

```python
def sanitize_data(data):
    """Remove outliers and invalid values."""
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.dropna()
    return data
```

---

## Deployment Architecture

### Development

```
Developer Machine
    ↓
Local Streamlit
    ↓
Local Data Cache
```

### Production (Future)

```
Load Balancer
    ↓
Multiple Streamlit Instances
    ↓
Redis Cache
    ↓
Database (PostgreSQL)
    ↓
External APIs
```

---

## Scalability Considerations

### Horizontal Scaling

- Stateless application design
- Session state in external store (Redis)
- Load balancing across instances

### Vertical Scaling

- Optimize numpy/pandas operations
- Use C extensions where needed
- Profile and optimize bottlenecks

### Data Scaling

- Incremental data updates
- Partitioned data storage
- Efficient caching strategy

---

## Monitoring & Observability

### Metrics Collection

```python
from quantlib_pro.observability import RealTimeMonitor

monitor = RealTimeMonitor()

with monitor.track('portfolio_optimization'):
    weights = optimizer.max_sharpe_ratio()
```

### Performance Profiling

```python
from quantlib_pro.observability import profile

@profile
def expensive_operation():
    # Automatically profiled
    pass
```

### Alerting

```python
monitor.set_alert_threshold(
    metric='portfolio_optimization',
    threshold_ms=1000,
    severity='warning'
)
```

---

## Future Enhancements

### Phase 1 (Q1 2026)
- REST API for programmatic access
- Webhook support for real-time alerts
- Database backend (PostgreSQL)

### Phase 2 (Q2 2026)
- Microservices architecture
- Message queue (RabbitMQ/Kafka)
- Container orchestration (Kubernetes)

### Phase 3 (Q3 2026)
- ML-based regime detection
- Reinforcement learning for portfolio optimization
- Real-time streaming data

---

## See Also

- [API Reference](api/README.md)
- [User Guide](guides/user_guide.md)
- [Deployment Guide](deployment.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
