# **QuantLib Pro API Reference**

Comprehensive REST API documentation for the enterprise quantitative finance platform. Built for institutional traders, portfolio managers, risk analysts, and quantitative researchers requiring production-grade financial modeling capabilities.

## **API Overview**

**Base URL**: `https://api.quantlibpro.com/v1`  
**Documentation**: `https://api.quantlibpro.com/docs`  
**Health Status**: `https://api.quantlibpro.com/health`

---

## **Authentication**

### **API Key Authentication**
```http
X-API-Key: your_enterprise_api_key
```

### **JWT Bearer Token** 
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### **Rate Limits**

| Tier | Requests/Hour | Burst Limit | Features |
|------|---------------|-------------|----------|
| Developer | 100 | 20/min | Core endpoints |
| Professional | 2,500 | 100/min | Advanced analytics |
| Enterprise | Unlimited | 500/min | Full platform access |

---

## **Core API Endpoints**

### **Portfolio Management**

#### **POST** `/portfolio/optimize`
Optimize portfolio weights using Modern Portfolio Theory.

```bash
curl -X POST "https://api.quantlibpro.com/v1/portfolio/optimize" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "assets": ["AAPL", "GOOGL", "MSFT", "TSLA"],
    "objective": "max_sharpe",
    "risk_free_rate": 0.02,
    "constraints": {
      "max_weight": 0.4,
      "min_weight": 0.05
    }
  }'
```

**Response:**
```json
{
  "optimal_weights": {
    "AAPL": 0.25,
    "GOOGL": 0.30, 
    "MSFT": 0.35,
    "TSLA": 0.10
  },
  "expected_return": 0.12,
  "volatility": 0.18,
  "sharpe_ratio": 0.67
}
```

#### **GET** `/portfolio/efficient-frontier`
Generate efficient frontier for portfolio optimization.

---

### **Risk Analytics**

#### **POST** `/risk/var`
Calculate Value-at-Risk using multiple methodologies.

```bash
curl -X POST "https://api.quantlibpro.com/v1/risk/var" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "portfolio_value": 1000000,
    "confidence_level": 0.95,
    "method": "historical",
    "horizon_days": 1
  }'
```

**Response:**
```json
{
  "var_95": 25000,
  "cvar_95": 35000,
  "method": "historical",
  "horizon_days": 1,
  "confidence_level": 0.95
}
```

---

### **Macro Economic Data (FRED Integration)**

#### **GET** `/macro/regime`
Get current macroeconomic regime assessment using real Federal Reserve data.

```bash
curl -X GET "https://api.quantlibpro.com/v1/macro/regime" \
  -H "X-API-Key: your_api_key"
```

**Response:**
```json
{
  "regime": "Expansion",
  "confidence": 0.78,
  "expansion_probability": 0.78,
  "recession_probability": 0.22,
  "indicators": {
    "gdp_growth": 1.4,
    "unemployment_rate": 4.3,
    "treasury_10y": 4.21,
    "inflation_rate": 3.2,
    "fed_funds_rate": 5.25
  },
  "last_updated": "2026-02-26T14:30:00Z"
}
```

#### **POST** `/macro/indicators`
Retrieve specific economic indicators from Federal Reserve data.

```bash
curl -X POST "https://api.quantlibpro.com/v1/macro/indicators" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "indicators": ["GDP_GROWTH", "UNEMPLOYMENT", "TREASURY_10Y"],
    "periods": 12
  }'
```

---
### **Options & Derivatives**

#### **POST** `/options/price`
Price options using Black-Scholes and calculate Greeks.

```bash
curl -X POST "https://api.quantlibpro.com/v1/options/price" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "spot_price": 100,
    "strike_price": 105,
    "time_to_expiry": 0.25,
    "risk_free_rate": 0.05,
    "volatility": 0.25,
    "option_type": "call"
  }'
```

**Response:**
```json
{
  "option_price": 2.85,
  "greeks": {
    "delta": 0.45,
    "gamma": 0.03,
    "theta": -0.05,
    "vega": 0.12,
    "rho": 0.08
  },
  "model": "black_scholes"
}
```

---

### **Market Data**

#### **GET** `/market/prices`
Retrieve real-time market prices with multi-provider failover.

```bash
curl -X GET "https://api.quantlibpro.com/v1/market/prices?symbols=AAPL,GOOGL,MSFT" \
  -H "X-API-Key: your_api_key"
```

---

## **Enterprise Support**

### **Enterprise Support Channels**

| Support Level | Contact Method | Response Time | Availability |
|---------------|----------------|---------------|-------------|
| **Community** | GitHub Issues | 48-72 hours | Business days |
| **Professional** | support@quantlibpro.com | 4-8 hours | Extended hours |
| **Enterprise** | Dedicated CSM | 1-2 hours | 24/7 |

### **Custom Integration Services**
- **Technical Consultation**: architecture@quantlibpro.com
- **Partnership Opportunities**: partnerships@quantlibpro.com  
- **Enterprise Sales**: enterprise@quantlibpro.com

### **SLA Guarantees**
- **Enterprise Tier**: 99.9% uptime guarantee
- **Response SLA**: <2 hours for critical issues
- **Data SLA**: <100ms latency for core endpoints

---

**Ready to integrate institutional-grade quantitative finance into your applications?**

*Contact our enterprise team for production API keys, custom endpoints, and dedicated support.*
print(f"Expected Return: {performance['return']:.2%}")
print(f"Volatility: {performance['volatility']:.2%}")
print(f"Sharpe Ratio: {performance['sharpe']:.2f}")
```

---

### Risk Metrics

**Module:** `quantlib_pro.risk`

#### `RiskCalculator`

Calculate Value at Risk (VaR) and Conditional VaR (CVaR).

```python
from quantlib_pro.risk import RiskCalculator

calculator = RiskCalculator()

# Parametric VaR (assumes normal distribution)
var = calculator.parametric_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

# Historical VaR
var = calculator.historical_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

# Monte Carlo VaR
var = calculator.monte_carlo_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000,
    n_simulations=10_000
)

# CVaR (Expected Shortfall)
cvar = calculator.cvar(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)
```

**Methods:**

- `parametric_var(returns, confidence_level=0.95, portfolio_value=1.0) -> float`
  - VaR assuming normal distribution
  - Fast but may underestimate tail risk

- `historical_var(returns, confidence_level=0.95, portfolio_value=1.0) -> float`
  - VaR from historical percentiles
  - Non-parametric, no distribution assumptions

- `monte_carlo_var(returns, confidence_level=0.95, portfolio_value=1.0, n_simulations=10000) -> float`
  - VaR from Monte Carlo simulation
  - Captures non-linear risk

- `cvar(returns, confidence_level=0.95, portfolio_value=1.0, method='historical') -> float`
  - Conditional VaR (Expected Shortfall)
  - Average loss beyond VaR threshold

**Example:**

```python
from quantlib_pro.risk import RiskCalculator
import pandas as pd

# Load portfolio returns
returns = pd.read_csv('portfolio_returns.csv')['returns']

calculator = RiskCalculator()

# Calculate 1-day 95% VaR for $1M portfolio
var_95 = calculator.historical_var(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

# Calculate CVaR (expected loss if VaR is exceeded)
cvar_95 = calculator.cvar(
    returns=returns,
    confidence_level=0.95,
    portfolio_value=1_000_000
)

print(f"95% VaR: ${var_95:,.0f}")
print(f"95% CVaR: ${cvar_95:,.0f}")
```

---

### Options Pricing

**Module:** `quantlib_pro.derivatives`

#### `BlackScholesPricer`

Price European options using Black-Scholes-Merton model.

```python
from quantlib_pro.derivatives import BlackScholesPricer

pricer = BlackScholesPricer(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    dividend_yield=0.0
)

# Option prices
call_price = pricer.call_price()
put_price = pricer.put_price()

# Greeks
delta = pricer.delta('call')
gamma = pricer.gamma()
vega = pricer.vega()
theta = pricer.theta('call')
rho = pricer.rho('call')
```

**Methods:**

- `call_price() -> float`
  - European call option price

- `put_price() -> float`
  - European put option price

- `delta(option_type='call') -> float`
  - Rate of change of option price w.r.t. underlying

- `gamma() -> float`
  - Rate of change of delta w.r.t. underlying

- `vega() -> float`
  - Sensitivity to volatility (per 1% change)

- `theta(option_type='call') -> float`
  - Time decay (per day)

- `rho(option_type='call') -> float`
  - Sensitivity to interest rate (per 1% change)

**Example:**

```python
from quantlib_pro.derivatives import BlackScholesPricer

# Price a call option on stock trading at $100
pricer = BlackScholesPricer(
    spot=100.0,
    strike=105.0,  # 5% out of the money
    time_to_maturity=0.25,  # 3 months
    risk_free_rate=0.05,
    volatility=0.25
)

call = pricer.call_price()
delta = pricer.delta('call')

print(f"Call Price: ${call:.2f}")
print(f"Delta: {delta:.4f}")
```

#### `MonteCarloEngine`

Price derivatives using Monte Carlo simulation.

```python
from quantlib_pro.derivatives import MonteCarloEngine

engine = MonteCarloEngine(
    spot=100.0,
    strike=100.0,
    time_to_maturity=1.0,
    risk_free_rate=0.05,
    volatility=0.2,
    n_simulations=100_000
)

# European option
call_price = engine.price_european_call()

# Path-dependent options
asian_price = engine.price_asian_call()
barrier_price = engine.price_barrier_call(barrier=110.0)
```

---

### Data Management

**Module:** `quantlib_pro.data`

#### `MarketDataProvider`

Fetch market data from multiple sources.

```python
from quantlib_pro.data import MarketDataProvider

provider = MarketDataProvider(source='yfinance')

# Get historical data
data = provider.get_historical_data(
    tickers=['AAPL', 'MSFT', 'GOOGL'],
    start_date='2020-01-01',
    end_date='2024-01-01'
)

# Get real-time quote
quote = provider.get_quote('AAPL')
```

**Supported Sources:**
- `yfinance` - Yahoo Finance
- `alpha_vantage` - Alpha Vantage API
- `iex` - IEX Cloud
- `polygon` - Polygon.io

---

### Backtesting

**Module:** `quantlib_pro.backtesting`

#### `Backtester`

Test trading strategies on historical data.

```python
from quantlib_pro.backtesting import Backtester, Strategy

class MyStrategy(Strategy):
    def generate_signals(self, data):
        # Your strategy logic
        return signals

backtester = Backtester(
    strategy=MyStrategy(),
    data=historical_data,
    initial_capital=100_000
)

results = backtester.run()
print(results.summary())
```

---

## Performance & Monitoring

### Profiling

**Module:** `quantlib_pro.observability`

```python
from quantlib_pro.observability import profile

@profile
def my_expensive_function():
    # Function will be profiled
    pass
```

### Monitoring

```python
from quantlib_pro.observability import RealTimeMonitor

monitor = RealTimeMonitor()

with monitor.track('portfolio_optimization'):
    # Code to monitor
    optimizer.max_sharpe_ratio()

# Get metrics
metrics = monitor.get_metrics('portfolio_optimization')
```

---

## Testing

### Load Testing

**Module:** `quantlib_pro.testing`

```python
from quantlib_pro.testing import LoadTester, LoadPattern

def portfolio_optimization_scenario():
    optimizer.max_sharpe_ratio()

tester = LoadTester()
results = tester.run_load_test(
    scenarios=[{'function': portfolio_optimization_scenario}],
    users=50,
    duration=60,
    pattern=LoadPattern.RAMP_UP
)
```

### Model Validation

```python
from quantlib_pro.testing import ModelValidator

validator = ModelValidator(tolerance=0.01)
results = validator.validate_all_models()
print(results.generate_report())
```

---

## See Also

- [User Guide](../guides/user_guide.md)
- [Tutorials](../tutorials/)
- [Architecture](../architecture.md)
- [Examples](../../examples/)
