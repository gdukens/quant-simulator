"""Celery task metadata model."""

from sqlalchemy import Column, String, Text, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from quantlib_pro.data.models.base import Base


class CeleryTaskMeta(Base):
    """Celery task metadata for async job tracking."""
    
    __tablename__ = "celery_task_meta"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(255), unique=True, nullable=False, index=True)  # Celery task UUID
    task_name = Column(String(255), nullable=False, index=True)  # e.g., "quantlib_pro.tasks.run_backtest"
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, started, success, failure, retry
    result = Column(JSON, nullable=True)  # Task result or error details
    traceback = Column(Text, nullable=True)  # Error traceback if failed
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Who initiated the task
    args = Column(JSON, nullable=True)  # Task arguments
    kwargs = Column(JSON, nullable=True)  # Task keyword arguments
    
    # Timing
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Retry tracking
    retries = Column(String(50), default="0", nullable=False)
    max_retries = Column(String(50), default="3", nullable=False)
    
    def __repr__(self):
        return f"<CeleryTaskMeta(task_id={self.task_id}, status={self.status}, task_name={self.task_name})>"
