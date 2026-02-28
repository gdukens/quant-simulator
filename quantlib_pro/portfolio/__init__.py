"""
Portfolio optimization suite.

Provides:
  - Mean-variance optimization (Markowitz)
  - Efficient frontier construction
  - Risk parity allocation
  - Black-Litterman model with investor views
  - Portfolio management and analysis tools
"""

# SDK Manager interface
from .manager import PortfolioManager

from .optimization import (
    PortfolioResult,
    max_sharpe_portfolio,
    min_volatility_portfolio,
    target_return_portfolio,
    efficient_frontier,
)

from .risk_parity import (
    risk_parity_portfolio,
    risk_budgeting_portfolio,
)

from .black_litterman import (
    MarketView,
    black_litterman,
    create_absolute_view,
    create_relative_view,
)

__all__ = [
    # SDK Manager
    "PortfolioManager",
    # Optimization
    "PortfolioResult",
    "max_sharpe_portfolio",
    "min_volatility_portfolio",
    "target_return_portfolio",
    "efficient_frontier",
    # Risk parity
    "risk_parity_portfolio",
    "risk_budgeting_portfolio",
    # Black-Litterman
    "MarketView",
    "black_litterman",
    "create_absolute_view",
    "create_relative_view",
]
