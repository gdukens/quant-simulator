"""
Risk Limit Framework — pre-trade and portfolio-level controls.

Checks are hierarchical:
  1. Position limits  (per-ticker max notional / shares)
  2. Portfolio limits (total VaR, max drawdown, concentration)
  3. Intra-day P&L limits (loss circuit-breaker)

All checks are non-blocking: they return a LimitCheckResult, never raise.
Callers decide whether to block execution.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)


class LimitStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"         # approaching limit (>80%)
    BREACH = "breach"           # limit violated
    DISABLED = "disabled"       # limit not configured for this entity


@dataclass
class LimitBreach:
    limit_name: str
    current_value: float
    limit_value: float
    utilisation: float          # current / limit
    status: LimitStatus


@dataclass
class LimitCheckResult:
    entity_id: str              # ticker or portfolio id
    checks: list[LimitBreach] = field(default_factory=list)
    checked_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def is_blocked(self) -> bool:
        return any(c.status == LimitStatus.BREACH for c in self.checks)

    @property
    def has_warnings(self) -> bool:
        return any(c.status == LimitStatus.WARNING for c in self.checks)

    @property
    def summary(self) -> str:
        if self.is_blocked:
            breaches = [c.limit_name for c in self.checks if c.status == LimitStatus.BREACH]
            return f"BLOCKED — limits breached: {breaches}"
        if self.has_warnings:
            warns = [c.limit_name for c in self.checks if c.status == LimitStatus.WARNING]
            return f"WARNING — approaching limits: {warns}"
        return "OK"


@dataclass
class PositionLimit:
    ticker: str
    max_notional: float = float("inf")      # USD notional
    max_shares: float = float("inf")
    max_concentration: float = 1.0          # fraction of portfolio


@dataclass
class PortfolioLimit:
    portfolio_id: str
    max_var_1d_95: float = float("inf")     # 1-day 95% VaR (positive number)
    max_cvar_1d_95: float = float("inf")    # 1-day 95% CVaR
    max_drawdown: float = 1.0               # max allowed drawdown fraction
    max_gross_leverage: float = float("inf")
    max_net_leverage: float = float("inf")
    max_single_position: float = 1.0        # max weight of any one holding
    intraday_loss_limit: float = float("inf")  # USD


class RiskLimitFramework:
    """
    Central registry and execution engine for all risk limits.

    Usage::

        framework = RiskLimitFramework()
        framework.set_position_limit(PositionLimit("AAPL", max_notional=1_000_000))
        framework.set_portfolio_limit(PortfolioLimit("port_001", max_var_1d_95=50_000))

        result = framework.check_position("AAPL", notional=800_000, portfolio_id="port_001")
        if result.is_blocked:
            log.error(result.summary)
    """

    def __init__(self) -> None:
        self._position_limits: dict[str, PositionLimit] = {}
        self._portfolio_limits: dict[str, PortfolioLimit] = {}

    # ── Configuration ─────────────────────────────────────────────────────────

    def set_position_limit(self, limit: PositionLimit) -> None:
        self._position_limits[limit.ticker.upper()] = limit
        log.info("Position limit set for %s: %s", limit.ticker, limit)

    def set_portfolio_limit(self, limit: PortfolioLimit) -> None:
        self._portfolio_limits[limit.portfolio_id] = limit
        log.info("Portfolio limit set for %s: %s", limit.portfolio_id, limit)

    # ── Checks ────────────────────────────────────────────────────────────────

    def check_position(
        self,
        ticker: str,
        notional: float,
        shares: Optional[float] = None,
        portfolio_weight: Optional[float] = None,
    ) -> LimitCheckResult:
        result = LimitCheckResult(entity_id=ticker.upper())
        lim = self._position_limits.get(ticker.upper())
        if lim is None:
            result.checks.append(
                LimitBreach(
                    "position_limit",
                    current_value=notional,
                    limit_value=float("inf"),
                    utilisation=0.0,
                    status=LimitStatus.DISABLED,
                )
            )
            return result

        result.checks.append(
            self._check_scalar("notional", notional, lim.max_notional)
        )
        if shares is not None:
            result.checks.append(
                self._check_scalar("shares", shares, lim.max_shares)
            )
        if portfolio_weight is not None:
            result.checks.append(
                self._check_scalar("concentration", portfolio_weight, lim.max_concentration)
            )
        return result

    def check_portfolio(
        self,
        portfolio_id: str,
        var_1d_95: Optional[float] = None,
        cvar_1d_95: Optional[float] = None,
        drawdown: Optional[float] = None,
        gross_leverage: Optional[float] = None,
        intraday_pnl_loss: Optional[float] = None,
    ) -> LimitCheckResult:
        result = LimitCheckResult(entity_id=portfolio_id)
        lim = self._portfolio_limits.get(portfolio_id)
        if lim is None:
            result.checks.append(
                LimitBreach(
                    "portfolio_limit",
                    current_value=0.0,
                    limit_value=float("inf"),
                    utilisation=0.0,
                    status=LimitStatus.DISABLED,
                )
            )
            return result

        pairs = [
            ("var_1d_95",       var_1d_95,          lim.max_var_1d_95),
            ("cvar_1d_95",      cvar_1d_95,         lim.max_cvar_1d_95),
            ("drawdown",        drawdown,            lim.max_drawdown),
            ("gross_leverage",  gross_leverage,      lim.max_gross_leverage),
            ("intraday_loss",   intraday_pnl_loss,   lim.intraday_loss_limit),
        ]
        for name, value, limit_val in pairs:
            if value is not None:
                result.checks.append(self._check_scalar(name, value, limit_val))

        return result

    # ── Internal ──────────────────────────────────────────────────────────────

    @staticmethod
    def _check_scalar(name: str, value: float, limit_val: float) -> LimitBreach:
        if limit_val == float("inf") or limit_val == 0:
            return LimitBreach(name, value, limit_val, 0.0, LimitStatus.DISABLED)
        utilisation = value / limit_val
        if utilisation > 1.0:
            status = LimitStatus.BREACH
        elif utilisation > 0.8:
            status = LimitStatus.WARNING
        else:
            status = LimitStatus.OK
        return LimitBreach(name, value, limit_val, utilisation, status)


# Module-level default instance
limits = RiskLimitFramework()
