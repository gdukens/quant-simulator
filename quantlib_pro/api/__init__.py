"""
REST API: FastAPI routers for all suites with auth middleware.

Week 11: API Layer - Main FastAPI application with all routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from quantlib_pro.api.health import router as health_router
from quantlib_pro.api.optimizations import startup_optimizations, shutdown_optimizations
from quantlib_pro.api.routers import (
    all_routers,
    macro_router,
    options_router,
    portfolio_router,
    regime_router,
    risk_router,
    volatility_router,
)

# =============================================================================
# Application Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown."""
    # Startup
    await startup_optimizations()
    yield
    # Shutdown
    await shutdown_optimizations()

# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="QuantLib Pro API",
    description="Enterprise quantitative finance platform with sub-500ms performance, "
                "Redis caching, async database pools, and real-time monitoring",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,  # Add performance optimization lifecycle
)

# =============================================================================
# Middleware
# =============================================================================

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# =============================================================================
# Register Routers
# =============================================================================

# Health check endpoints
app.include_router(health_router)

# Core API routers
app.include_router(portfolio_router, prefix="/api/v1")
app.include_router(options_router, prefix="/api/v1")
app.include_router(risk_router, prefix="/api/v1")
app.include_router(regime_router, prefix="/api/v1")
app.include_router(volatility_router, prefix="/api/v1")
app.include_router(macro_router, prefix="/api/v1")

# =============================================================================
# Root Endpoints
# =============================================================================

@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "QuantLib Pro API",
        "version": "2.1.0",
        "status": "running",
        "performance": "optimized",
        "features": [
            "Redis caching (<50ms)",
            "Async database pools",
            "Sub-500ms SLA",
            "Connection pooling"
        ],
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }

@app.get("/metrics", tags=["monitoring"])
async def performance_metrics():
    """Get API performance metrics."""
    from quantlib_pro.api.optimizations import performance_monitor
    
    report = performance_monitor.get_performance_report()
    
    return {
        "performance_report": report,
        "sla_target": "500ms",
        "optimization_status": "active",
        "cache_layers": ["L1: In-Memory", "L2: Redis", "L3: Database"],
        "monitoring": {
            "prometheus_enabled": True,
            "grafana_dashboard": True,
            "alerts_configured": True
        }
    }


@app.get("/version", tags=["root"])
async def version():
    """Get API version information."""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "build": "production",
    }


# =============================================================================
# Exports
# =============================================================================

__all__ = [
    # FastAPI app
    "app",
    
    # Routers
    "health_router",
    "portfolio_router",
    "options_router",
    "risk_router",
    "regime_router",
    "volatility_router",
    "macro_router",
    "all_routers",
]
