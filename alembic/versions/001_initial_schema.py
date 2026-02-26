"""Initial schema with users, portfolios, holdings, audit logs, backtest results, and celery tasks.

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('username', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('api_key', sa.String(255), unique=True, nullable=True, index=True),
        sa.Column('tier', sa.String(20), default='free', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create portfolios table
    op.create_table(
        'portfolios',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('initial_capital', sa.DECIMAL(15, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    
    # Create holdings table
    op.create_table(
        'holdings',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('portfolio_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('portfolios.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('ticker', sa.String(10), nullable=False, index=True),
        sa.Column('shares', sa.DECIMAL(15, 4), nullable=False),
        sa.Column('avg_cost', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.UniqueConstraint('portfolio_id', 'ticker', name='uq_portfolio_ticker'),
    )
    
    # Create audit_log table
    op.create_table(
        'audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('action', sa.String(100), nullable=False, index=True),
        sa.Column('resource_type', sa.String(50), nullable=False, index=True),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('details', postgresql.JSON, nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    
    # Create backtest_results table
    op.create_table(
        'backtest_results',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('strategy_name', sa.String(100), nullable=False, index=True),
        sa.Column('start_date', sa.DateTime(timezone=False), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=False), nullable=False),
        sa.Column('total_return', sa.DECIMAL(10, 4), nullable=True),
        sa.Column('sharpe_ratio', sa.DECIMAL(8, 4), nullable=True),
        sa.Column('max_drawdown', sa.DECIMAL(8, 4), nullable=True),
        sa.Column('volatility', sa.DECIMAL(8, 4), nullable=True),
        sa.Column('alpha', sa.DECIMAL(8, 4), nullable=True),
        sa.Column('beta', sa.DECIMAL(8, 4), nullable=True),
        sa.Column('equity_curve', postgresql.JSON, nullable=True),
        sa.Column('trades', postgresql.JSON, nullable=True),
        sa.Column('config', postgresql.JSON, nullable=False),
        sa.Column('status', sa.String(20), default='completed', nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('execution_time_seconds', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False, index=True),
    )
    
    # Create celery_task_meta table
    op.create_table(
        'celery_task_meta',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('task_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('task_name', sa.String(255), nullable=False, index=True),
        sa.Column('status', sa.String(20), default='pending', nullable=False, index=True),
        sa.Column('result', postgresql.JSON, nullable=True),
        sa.Column('traceback', sa.Text, nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('args', postgresql.JSON, nullable=True),
        sa.Column('kwargs', postgresql.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('retries', sa.String(50), default='0', nullable=False),
        sa.Column('max_retries', sa.String(50), default='3', nullable=False),
    )


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('celery_task_meta')
    op.drop_table('backtest_results')
    op.drop_table('audit_log')
    op.drop_table('holdings')
    op.drop_table('portfolios')
    op.drop_table('users')
