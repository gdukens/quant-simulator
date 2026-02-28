# QuantLib Pro SDK: Scientific Documentation

[![PyPI version](https://badge.fury.io/py/quantlib-pro.svg)](https://badge.fury.io/py/quantlib-pro)
[![Documentation Status](https://readthedocs.org/projects/quantlib-pro/badge/?version=latest)](https://quantlib-pro.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Enterprise Quantitative Finance Toolkit with Rigorous Mathematical Foundations**

```{toctree}
:maxdepth: 3
:caption: Getting Started

quickstart
installation
configuration
```

```{toctree}
:maxdepth: 3
:caption: Mathematical Foundations

mathematical_foundations/index
mathematical_foundations/probability_theory
mathematical_foundations/stochastic_processes
mathematical_foundations/martingale_theory
mathematical_foundations/ito_calculus
mathematical_foundations/pde_methods
```

```{toctree}
:maxdepth: 3
:caption: Portfolio Theory

portfolio_theory/index
portfolio_theory/modern_portfolio_theory
portfolio_theory/capital_asset_pricing
portfolio_theory/arbitrage_pricing_theory
portfolio_theory/factor_models
portfolio_theory/optimization_methods
```

```{toctree}
:maxdepth: 3
:caption: Risk Management

risk_management/index
risk_management/value_at_risk
risk_management/expected_shortfall
risk_management/coherent_risk_measures
risk_management/extreme_value_theory
risk_management/copula_methods
```

```{toctree}
:maxdepth: 3
:caption: Derivatives Pricing

derivatives/index
derivatives/black_scholes_framework
derivatives/interest_rate_models
derivatives/credit_risk_models
derivatives/exotic_options
derivatives/numerical_methods
```

```{toctree}
:maxdepth: 3
:caption: Volatility Modeling

volatility/index
volatility/garch_models
volatility/stochastic_volatility
volatility/volatility_surfaces
volatility/implied_volatility
volatility/jump_diffusion_models
```

```{toctree}
:maxdepth: 3
:caption: Market Microstructure

microstructure/index
microstructure/order_flow_models
microstructure/market_impact_models
microstructure/execution_algorithms
microstructure/high_frequency_models
```

```{toctree}
:maxdepth: 3
:caption: API Reference

api/index
api/sdk
api/portfolio
api/risk
api/options
api/volatility
api/data
api/analytics
```

```{toctree}
:maxdepth: 3
:caption: Examples & Tutorials

examples/index
examples/portfolio_optimization
examples/risk_analytics
examples/options_strategies
examples/volatility_forecasting
examples/backtesting
```

```{toctree}
:maxdepth: 2
:caption: Development

development/contributing
development/testing
development/performance
```

## Overview

QuantLib Pro is an enterprise-grade quantitative finance toolkit that provides rigorous mathematical implementations of modern financial theory. Built upon measure-theoretic probability theory and stochastic calculus, the library combines theoretical foundations with practical applications, offering both academic depth and production readiness.

### Mathematical Foundations

The library is constructed upon several pillars of mathematical finance:

#### Probability Theory and Measure Theory
All stochastic models are grounded in measure-theoretic probability:
- **Probability Spaces**: $(\Omega, \mathcal{F}, \mathbb{P})$ with σ-algebras and probability measures
- **Filtrations**: Information flow modeling through $(\mathcal{F}_t)_{t \geq 0}$
- **Conditional Expectations**: $\mathbb{E}[X|\mathcal{G}]$ with tower property and measurability
- **Convergence**: Almost sure, in probability, and $L^p$ convergence theorems

#### Stochastic Processes and Martingale Theory
Core processes for asset price modeling:
- **Brownian Motion**: $(W_t)_{t \geq 0}$ with independent increments and continuous paths
- **Geometric Brownian Motion**: $S_t = S_0 \exp((\mu - \frac{\sigma^2}{2})t + \sigma W_t)$
- **Martingales**: $\mathbb{E}[M_t|\mathcal{F}_s] = M_s$ for risk-neutral valuation
- **Girsanov's Theorem**: Change of measure for risk-neutral pricing

#### Itô Calculus and Stochastic Integration
Foundation for derivatives pricing:
- **Stochastic Integrals**: $\int_0^t H_s dW_s$ with Itô isometry
- **Itô's Formula**: $df(X_t) = f'(X_t)dX_t + \frac{1}{2}f''(X_t)(dX_t)^2$
- **SDEs**: $dX_t = \mu(t,X_t)dt + \sigma(t,X_t)dW_t$ with existence and uniqueness
- **Feynman-Kac**: Connection between SDEs and PDEs

#### Partial Differential Equations
Numerical methods for complex derivatives:
- **Black-Scholes PDE**: $\frac{\partial V}{\partial t} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 V}{\partial S^2} + rS\frac{\partial V}{\partial S} - rV = 0$
- **Multi-Asset PDEs**: Stochastic volatility and jump-diffusion extensions
- **American Options**: Free boundary problems and linear complementarity
- **Numerical Methods**: Finite differences, finite elements, and spectral methods

### Portfolio Theory Framework

Modern portfolio theory with mathematical rigor:

#### Mean-Variance Optimization
Markowitz framework with explicit solutions:
- **Efficient Frontier**: $w^*(\mu_0) = g + h\mu_0$ where $g,h$ depend on $(\Sigma^{-1}, A, B, C)$
- **Tangency Portfolio**: $w_t = \frac{\Sigma^{-1}(\mu - r_f\mathbf{1})}{\mathbf{1}^T\Sigma^{-1}(\mu - r_f\mathbf{1})}$
- **Capital Market Line**: $\mu_p = r_f + SR_{max} \cdot \sigma_p$

#### Asset Pricing Models
Equilibrium and arbitrage theories:
- **CAPM**: $\mathbb{E}[R_i] = r_f + \beta_i(\mathbb{E}[R_M] - r_f)$
- **APT**: $\mathbb{E}[R_i] = r_f + \sum_{j=1}^K \beta_{ij}\lambda_j$
- **Fama-French**: Multi-factor risk premium models

#### Risk-Based Methods
Alternative portfolio construction:
- **Risk Parity**: Equal risk contribution $RC_i = \frac{\sigma_p}{n}$
- **Maximum Diversification**: $\max \frac{w^T\sigma}{\sqrt{w^T\Sigma w}}$
- **Black-Litterman**: Bayesian portfolio optimization with views

### Risk Management Theory

Comprehensive risk measurement and management:

#### Value-at-Risk and Beyond
Risk measures with mathematical properties:
- **VaR**: $VaR_\alpha = -\inf\{x : F(x) ≥ \alpha\}$ where $F$ is the loss distribution
- **Expected Shortfall**: $ES_\alpha = \mathbb{E}[L | L ≥ VaR_\alpha]$
- **Coherent Risk Measures**: Monotonicity, translation invariance, homogeneity, subadditivity
- **Spectral Risk Measures**: $\rho(X) = \int_0^1 \phi(p) F_X^{-1}(p) dp$

#### Extreme Value Theory
Tail risk modeling:
- **Generalized Extreme Value**: $G(x) = \exp\{-(1+\xi\frac{x-\mu}{\sigma})^{-1/\xi}\}$
- **Peaks Over Threshold**: Generalized Pareto distribution for tail modeling
- **Hill Estimator**: $\hat{\xi}_k = \frac{1}{k}\sum_{i=1}^k \log(X_{(n-i+1)}) - \log(X_{(n-k)})$

### Key Features

- **Mathematical Rigor**: All models implemented with complete theoretical foundations and proofs
- **Production Ready**: Enterprise-grade architecture with comprehensive testing and validation
- **Extensible**: Modular design allowing easy customization and model extensions
- **Performance Optimized**: Vectorized operations, efficient algorithms, and parallel processing
- **Well Documented**: Comprehensive mathematical derivations and practical implementation guides
- **Research Integration**: Direct connection between academic literature and implementation

### Mathematical Scope

The library encompasses the complete mathematical framework of quantitative finance:

$$\text{QuantLib Pro} = \bigcup_{i} \{\text{Probability}, \text{Stochastic Calculus}, \text{Portfolio Theory}, \text{Risk Management}, \text{Derivatives}\}$$

Each component maintains mathematical consistency and provides both theoretical insights and practical tools for financial modeling and analysis.

## Quick Example

```python
import numpy as np
from quantlib_pro import QuantLibSDK

# Initialize SDK
sdk = QuantLibSDK()

# Portfolio optimization using Modern Portfolio Theory
symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']
data = sdk.data.get_price_data(symbols, period='2y')
returns = data.pct_change().dropna()

# Markowitz mean-variance optimization
mu = returns.mean() * 252  # Expected annual returns
Sigma = returns.cov() * 252  # Covariance matrix

# Solve: max μᵀw - (γ/2)wᵀΣw subject to 1ᵀw = 1
result = sdk.portfolio.optimize_portfolio(mu, Sigma, risk_aversion=1.0)
print(f"Optimal weights: {result['optimal_weights']}")

# Value at Risk using parametric method
# VaR_α = -μ - Φ⁻¹(α)σ for normal distribution
portfolio_returns = (returns * list(result['optimal_weights'].values())).sum(axis=1)
var_95 = sdk.risk.calculate_var(portfolio_returns, confidence_level=0.05)
print(f"Portfolio VaR (95%): {var_95:.4f}")

# Black-Scholes option pricing
# C₀ = S₀Φ(d₁) - Ke⁻ʳᵀΦ(d₂)
call_price = sdk.options.black_scholes(S=100, K=105, T=0.25, r=0.05, sigma=0.2)
print(f"Call option price: ${call_price:.4f}")
```

## Installation

Install from PyPI:

```bash
pip install quantlib-pro
```

For development installation:

```bash
git clone https://github.com/quantlib-pro/quantlib-pro.git
cd quantlib-pro
pip install -e .[dev,all]
```

## Academic Citations

When using QuantLib Pro in academic research, please cite:

```bibtex
@software{quantlib_pro_2024,
  title={QuantLib Pro: Enterprise Quantitative Finance SDK},
  author={QuantLib Pro Team},
  year={2024},
  url={https://github.com/quantlib-pro/quantlib-pro},
  version={1.0.0}
}
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.