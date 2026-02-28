# Mathematical Foundations

This section provides the rigorous mathematical framework underlying all quantitative finance methodologies implemented in QuantLib Pro. We build from first principles, establishing the mathematical machinery necessary for modern financial modeling.

## Overview of Mathematical Framework

The mathematical foundation of quantitative finance rests upon several pillars:

```{math}
:label: foundation_pillars

\text{Quantitative Finance} \subseteq \left\{
\begin{array}{l}
\text{Probability Theory} \\  
\text{Stochastic Processes} \\
\text{Martingale Theory} \\
\text{Stochastic Calculus} \\
\text{Partial Differential Equations} \\
\text{Optimization Theory} \\
\text{Statistical Inference}
\end{array}
\right\}
```

## Core Mathematical Concepts

### 1. Probability Spaces and Filtrations

Financial modeling requires a rigorous probabilistic framework. We work within a complete probability space $(\Omega, \mathcal{F}, \mathbb{P})$ where:

- $\Omega$ is the sample space of all possible market scenarios
- $\mathcal{F}$ is a $\sigma$-algebra representing observable events
- $\mathbb{P}$ is a probability measure under which we evaluate expectations

**Information Structure**: The flow of information is modeled through a filtration $\mathbb{F} = (\mathcal{F}_t)_{t \geq 0}$:

```{math}
:label: filtration

\mathcal{F}_s \subseteq \mathcal{F}_t \subseteq \mathcal{F} \quad \text{for all } 0 \leq s \leq t
```

### 2. Stochastic Processes in Finance

Asset prices are modeled as adapted stochastic processes. The canonical geometric Brownian motion model:

```{math}
:label: gbm

dS_t = \mu S_t dt + \sigma S_t dW_t
```

where:
- $S_t$ is the asset price at time $t$
- $\mu$ is the drift coefficient (expected return)
- $\sigma$ is the volatility coefficient
- $W_t$ is a standard Brownian motion

### 3. Martingale Theory and No-Arbitrage

The fundamental theorem of asset pricing establishes the equivalence between:
- Absence of arbitrage opportunities
- Existence of an equivalent martingale measure

Under the risk-neutral measure $\mathbb{Q}$:

```{math}
:label: risk_neutral

S_t = \mathbb{E}^{\mathbb{Q}}\left[e^{-r(T-t)} S_T \mid \mathcal{F}_t\right]
```

### 4. Itô's Formula

For a twice-differentiable function $f(t, S_t)$ where $S_t$ follows {eq}`gbm`:

```{math}
:label: ito_formula

df = \left(\frac{\partial f}{\partial t} + \mu S \frac{\partial f}{\partial S} + \frac{1}{2}\sigma^2 S^2 \frac{\partial^2 f}{\partial S^2}\right)dt + \sigma S \frac{\partial f}{\partial S}dW_t
```

This is fundamental for derivatives pricing and risk management.

## Chapter Organization

```{toctree}
:maxdepth: 2

probability_theory
stochastic_processes  
martingale_theory
ito_calculus
pde_methods
optimization_theory
statistical_methods
```

Each chapter builds upon previous concepts while maintaining mathematical rigor. All theoretical results are accompanied by implementation details showing how abstract mathematics translates to practical algorithms.

## Notation Conventions

Throughout this documentation, we adhere to standard mathematical finance notation:

### Probability and Expectation
- $\mathbb{P}$ - Physical (real-world) probability measure
- $\mathbb{Q}$ - Risk-neutral probability measure  
- $\mathbb{E}[\cdot]$ - Expectation operator
- $\mathbb{E}^{\mathbb{Q}}[\cdot]$ - Expectation under risk-neutral measure
- $\text{Var}[\cdot]$ - Variance operator
- $\text{Cov}[\cdot, \cdot]$ - Covariance operator

### Stochastic Processes
- $W_t$ - Standard Brownian motion
- $dW_t$ - Brownian increment
- $\mathcal{F}_t$ - Information available at time $t$
- $\tau$ - Stopping time
- $\mathbb{F}$-adapted - Process adapted to filtration $\mathbb{F}$

### Financial Variables
- $S_t$ - Asset price at time $t$
- $r$ - Risk-free interest rate
- $\sigma$ - Volatility parameter
- $\mu$ - Drift parameter
- $T$ - Maturity/expiration time
- $K$ - Strike price

### Portfolio Theory
- $w_i$ - Portfolio weight for asset $i$
- $\boldsymbol{w}$ - Portfolio weight vector
- $\boldsymbol{\mu}$ - Expected return vector
- $\boldsymbol{\Sigma}$ - Covariance matrix
- $\gamma$ - Risk aversion parameter

### Risk Measures
- $\text{VaR}_\alpha$ - Value at Risk at confidence level $\alpha$
- $\text{CVaR}_\alpha$ - Conditional Value at Risk
- $\rho[\cdot]$ - Generic risk measure

This notation provides consistency across all mathematical derivations and implementations.