"""TimescaleDB hypertable models for time-series data."""

from sqlalchemy import Column, String, DECIMAL, DateTime, Integer
from sqlalchemy.dialects.postgresql import JSONB

from quantlib_pro.data.models.base import Base


class Price(Base):
    """Stock price time-series (will be converted to hypertable)."""
    
    __tablename__ = "prices"
    
    time = Column(DateTime(timezone=False), primary_key=True, nullable=False)
    ticker = Column(String(10), primary_key=True, nullable=False, index=True)
    open = Column(DECIMAL(10, 4), nullable=False)
    high = Column(DECIMAL(10, 4), nullable=False)
    low = Column(DECIMAL(10, 4), nullable=False)
    close = Column(DECIMAL(10, 4), nullable=False)
    volume = Column(Integer, nullable=False)
    adjusted_close = Column(DECIMAL(10, 4), nullable=True)
    
    def __repr__(self):
        return f"<Price(ticker={self.ticker}, time={self.time}, close={self.close})>"


class Return(Base):
    """Return time-series (will be converted to hypertable)."""
    
    __tablename__ = "returns"
    
    time = Column(DateTime(timezone=False), primary_key=True, nullable=False)
    ticker = Column(String(10), primary_key=True, nullable=False, index=True)
    simple_return = Column(DECIMAL(12, 8), nullable=False)
    log_return = Column(DECIMAL(12, 8), nullable=False)
    
    def __repr__(self):
        return f"<Return(ticker={self.ticker}, time={self.time}, log_return={self.log_return})>"


class RegimeState(Base):
    """Market regime state time-series (will be converted to hypertable)."""
    
    __tablename__ = "regime_states"
    
    time = Column(DateTime(timezone=False), primary_key=True, nullable=False)
    ticker = Column(String(10), primary_key=True, nullable=False, index=True)
    regime = Column(Integer, nullable=False)  # 0=low_vol, 1=high_vol, 2=crisis
    regime_label = Column(String(20), nullable=False)
    transition_probability = Column(DECIMAL(8, 6), nullable=True)
    metadata = Column(JSONB, nullable=True)  # Additional regime metrics
    
    def __repr__(self):
        return f"<RegimeState(ticker={self.ticker}, time={self.time}, regime={self.regime_label})>"
