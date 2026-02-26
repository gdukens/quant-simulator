"""Backtest result model."""

from sqlalchemy import Column, String, Text, DateTime, JSON, DECIMAL
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from quantlib_pro.data.models.base import Base


class BacktestResult(Base):
    """Backtest result storage."""
    
    __tablename__ = "backtest_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    strategy_name = Column(String(100), nullable=False, index=True)
    start_date = Column(DateTime(timezone=False), nullable=False)
    end_date = Column(DateTime(timezone=False), nullable=False)
    
    # Performance metrics
    total_return = Column(DECIMAL(10, 4), nullable=True)
    sharpe_ratio = Column(DECIMAL(8, 4), nullable=True)
    max_drawdown = Column(DECIMAL(8, 4), nullable=True)
    volatility = Column(DECIMAL(8, 4), nullable=True)
    alpha = Column(DECIMAL(8, 4), nullable=True)
    beta = Column(DECIMAL(8, 4), nullable=True)
    
    # Detailed results
    equity_curve = Column(JSON, nullable=True)  # Time series of portfolio values
    trades = Column(JSON, nullable=True)  # List of all trades executed
    config = Column(JSON, nullable=False)  # Strategy configuration
    
    # Metadata
    status = Column(String(20), default="completed", nullable=False)  # completed, failed, running
    error_message = Column(Text, nullable=True)
    execution_time_seconds = Column(DECIMAL(10, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<BacktestResult(id={self.id}, strategy={self.strategy_name}, sharpe={self.sharpe_ratio})>"
