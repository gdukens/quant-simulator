"""Create TimescaleDB hypertables for time-series data.

Revision ID: 002_timescaledb_hypertables
Revises: 001_initial_schema
Create Date: 2025-01-16

Note: This migration should be run against the TimescaleDB instance, not PostgreSQL.
Use TIMESCALE_URL environment variable to connect.

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '002_timescaledb_hypertables'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create TimescaleDB hypertables for time-series data."""
    
    # Create prices table
    op.create_table(
        'prices',
        sa.Column('time', sa.DateTime(timezone=False), primary_key=True, nullable=False),
        sa.Column('ticker', sa.String(10), primary_key=True, nullable=False, index=True),
        sa.Column('open', sa.DECIMAL(10, 4), nullable=False),
        sa.Column('high', sa.DECIMAL(10, 4), nullable=False),
        sa.Column('low', sa.DECIMAL(10, 4), nullable=False),
        sa.Column('close', sa.DECIMAL(10, 4), nullable=False),
        sa.Column('volume', sa.Integer, nullable=False),
        sa.Column('adjusted_close', sa.DECIMAL(10, 4), nullable=True),
    )
    
    # Convert prices to hypertable (partition by time, 1 day chunks)
    op.execute("SELECT create_hypertable('prices', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);")
    
    # Create returns table
    op.create_table(
        'returns',
        sa.Column('time', sa.DateTime(timezone=False), primary_key=True, nullable=False),
        sa.Column('ticker', sa.String(10), primary_key=True, nullable=False, index=True),
        sa.Column('simple_return', sa.DECIMAL(12, 8), nullable=False),
        sa.Column('log_return', sa.DECIMAL(12, 8), nullable=False),
    )
    
    # Convert returns to hypertable
    op.execute("SELECT create_hypertable('returns', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);")
    
    # Create regime_states table
    op.create_table(
        'regime_states',
        sa.Column('time', sa.DateTime(timezone=False), primary_key=True, nullable=False),
        sa.Column('ticker', sa.String(10), primary_key=True, nullable=False, index=True),
        sa.Column('regime', sa.Integer, nullable=False),
        sa.Column('regime_label', sa.String(20), nullable=False),
        sa.Column('transition_probability', sa.DECIMAL(8, 6), nullable=True),
        sa.Column('metadata', postgresql.JSONB, nullable=True),
    )
    
    # Convert regime_states to hypertable
    op.execute("SELECT create_hypertable('regime_states', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);")
    
    # Create indexes for faster queries
    op.create_index('idx_prices_ticker_time', 'prices', ['ticker', 'time'])
    op.create_index('idx_returns_ticker_time', 'returns', ['ticker', 'time'])
    op.create_index('idx_regime_states_ticker_time', 'regime_states', ['ticker', 'time'])
    
    # Create continuous aggregates for daily OHLCV (useful for faster queries)
    op.execute("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS prices_daily
        WITH (timescaledb.continuous) AS
        SELECT 
            time_bucket('1 day', time) AS day,
            ticker,
            FIRST(open, time) AS open,
            MAX(high) AS high,
            MIN(low) AS low,
            LAST(close, time) AS close,
            SUM(volume) AS volume
        FROM prices
        GROUP BY day, ticker
        WITH NO DATA;
    """)
    
    # Add refresh policy (refresh every hour)
    op.execute("""
        SELECT add_continuous_aggregate_policy('prices_daily',
            start_offset => INTERVAL '1 month',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour',
            if_not_exists => TRUE);
    """)


def downgrade() -> None:
    """Drop TimescaleDB hypertables and views."""
    # Drop continuous aggregate
    op.execute("DROP MATERIALIZED VIEW IF EXISTS prices_daily;")
    
    # Drop indexes
    op.drop_index('idx_regime_states_ticker_time')
    op.drop_index('idx_returns_ticker_time')
    op.drop_index('idx_prices_ticker_time')
    
    # Drop tables (hypertables are automatically handled)
    op.drop_table('regime_states')
    op.drop_table('returns')
    op.drop_table('prices')
