"""Market data pipeline: resilient fetching, multi-tier caching, quality validation, multi-provider support."""

# SDK Manager interface
from .manager import DataManager

from quantlib_pro.data.cache import get_dataframe, set_dataframe
from quantlib_pro.data.fetcher import DataFetchError, ResilientDataFetcher
from quantlib_pro.data.quality import (
    DataQualityError,
    DataQualityValidator,
    OHLCV_CONTRACT,
    PORTFOLIO_CONTRACT,
    QualityContract,
    QualityReport,
)

# Database connections and models
try:
    from quantlib_pro.data.database import (
        postgres_engine,
        timescale_engine,
        get_postgres_session,
        get_timescale_session,
        get_postgres_session_sync,
        get_timescale_session_sync,
        init_db,
        drop_db,
    )
    from quantlib_pro.data.models import (
        Base,
        User,
        Portfolio,
        Holding,
        AuditLog,
        BacktestResult,
        CeleryTaskMeta,
        Price,
        Return,
        RegimeState,
    )
except ImportError:
    # Database not configured yet
    postgres_engine = None
    timescale_engine = None
    get_postgres_session = None
    get_timescale_session = None
# Legacy providers (providers.py) - kept for backward compatibility
try:
    from quantlib_pro.data.providers_legacy import (
        DataProvider,
        YahooFinanceProvider,
        CSVProvider,
        SimulatedProvider,
        DataProviderFactory,
        MultiProviderAggregator,
    )
except ImportError:
    # If legacy providers don't exist, skip them
    DataProvider = None
    YahooFinanceProvider = None
    CSVProvider = None
    SimulatedProvider = None
    DataProviderFactory = None
    MultiProviderAggregator = None

__all__ = [
    # SDK Manager
    "DataManager",
    # fetcher
    "ResilientDataFetcher",
    "DataFetchError",
    # cache helpers
    "get_dataframe",
    "set_dataframe",
    # quality
    "DataQualityValidator",
    "DataQualityError",
    "QualityContract",
    "QualityReport",
    "OHLCV_CONTRACT",
    "PORTFOLIO_CONTRACT",
    # database connections
    "postgres_engine",
    "timescale_engine",
    "get_postgres_session",
    "get_timescale_session",
    "get_postgres_session_sync",
    "get_timescale_session_sync",
    "init_db",
    "drop_db",
    # database models
    "Base",
    "User",
    "Portfolio",
    "Holding",
    "AuditLog",
    "BacktestResult",
    "CeleryTaskMeta",
    "Price",
    "Return",
    "RegimeState",
]

# Add legacy providers to __all__ if they're available
if DataProvider is not None:
    __all__.extend([
        "DataProvider",
        "YahooFinanceProvider",
        "CSVProvider",
        "SimulatedProvider",
        "DataProviderFactory",
        "MultiProviderAggregator",
    ])
