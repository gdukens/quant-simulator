"""
REST API: FastAPI routers for all suites with auth middleware.

Week 11: API Layer - Main FastAPI application with all routers.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from quantlib_pro.api.health import router as health_router
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
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="QuantLib Pro API",
    description="Quantitative finance platform with portfolio optimization, "
                "options pricing, risk analysis, and market regime detection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
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
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
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
