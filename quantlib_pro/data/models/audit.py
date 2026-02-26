"""Audit log model."""

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from quantlib_pro.data.models.base import Base


class AuditLog(Base):
    """Audit log for tracking all system actions."""
    
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # NULL for system actions
    action = Column(String(100), nullable=False, index=True)  # e.g., "portfolio.create", "backtest.run"
    resource_type = Column(String(50), nullable=False, index=True)  # e.g., "portfolio", "backtest"
    resource_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    details = Column(JSON, nullable=True)  # JSON payload with action details
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(action={self.action}, user_id={self.user_id}, timestamp={self.timestamp})>"
