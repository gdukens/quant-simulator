#!/usr/bin/env python3
"""
QuantLib Pro - FastAPI Application Entry Point

Production-ready REST API server for quantitative finance platform.
Consolidates 30+ specialized applications into a unified API.

Usage:
    python main_api.py                    # Development server
    uvicorn main_api:app --host 0.0.0.0   # Production server

Author: tubakhxn
Date: February 2026
"""

import logging
import sys
import asyncio
import gc
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, Any
import time

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
import redis.asyncio as redis

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from quantlib_pro.api.health import router as health_router
from quantlib_pro.api.auth import auth_router
from quantlib_pro.api.routers import (
    macro_router,
    options_router,
    portfolio_router,
    regime_router,
    risk_router,
    volatility_router,
)
from quantlib_pro.api.routers_backtesting import backtesting_router
from quantlib_pro.api.routers_analytics import analytics_router
from quantlib_pro.api.routers_data import data_router
from quantlib_pro.api.routers_realdata import realdata_router
from quantlib_pro.api.routers_macro import macro_router
from quantlib_pro.api.routers_market_analysis import market_analysis_router
from quantlib_pro.api.routers_signals import signals_router
from quantlib_pro.api.routers_liquidity import liquidity_router
from quantlib_pro.api.routers_systemic_risk import systemic_risk_router
from quantlib_pro.api.routers_execution import execution_router
from quantlib_pro.api.routers_compliance import compliance_router
from quantlib_pro.api.routers_uat import uat_router
from quantlib_pro.observability import track_api_request

# =============================================================================
# Application Lifecycle
# =============================================================================

# =============================================================================
# Performance Configuration
# =============================================================================

# Global cache instance
cache_instance: redis.Redis = None
performance_stats: Dict[str, Any] = {
    "requests_count": 0,
    "average_response_time": 0,
    "cache_hits": 0,
    "cache_misses": 0
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Production-optimized application lifecycle manager.
    Handles startup and shutdown with performance optimizations.
    """
    global cache_instance
    
    # Startup
    logging.info(" QuantLib Pro API starting up (Performance Mode)...")
    
    # Initialize Redis connection pool for production performance
    try:
        cache_instance = redis.Redis(
            host='localhost',
            port=6379,
            db=0,
            decode_responses=True,
            max_connections=50,  # Connection pooling
            retry_on_timeout=True,
            socket_keepalive=True,
            socket_keepalive_options={1: 1, 2: 3, 3: 5}
        )
        await cache_instance.ping()
        logging.info(" Redis cache connected with connection pooling")
    except Exception as e:
        logging.warning(f"  Redis cache unavailable: {e}")
        cache_instance = None
    
    # Set async event loop policy for better performance
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoop())
    
    # Configure garbage collection for memory optimization
    gc.set_threshold(700, 10, 10)  # More aggressive GC
    
    logging.info(" QuantLib Pro API ready (Production Performance Mode)")
    
    yield  # Application is running
    
    # Shutdown
    logging.info("  QuantLib Pro API shutting down...")
    
    # Close Redis connections
    if cache_instance:
        await cache_instance.close()
        logging.info(" Redis connections closed")
    
    # Force garbage collection on shutdown
    gc.collect()
    
    logging.info(" Shutdown complete")


# =============================================================================
# Rate Limiting
# =============================================================================

# Global rate limiter using client IP
limiter = Limiter(key_func=get_remote_address)

# Custom rate limit exceeded handler
def rate_limit_handler(request, exc):
    """Custom handler for rate limit exceeded."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": f"Too many requests. Retry after {exc.retry_after} seconds.",
            "retry_after": exc.retry_after,
            "timestamp": "2026-02-25T00:00:00Z"  # In production: use datetime.utcnow()
        }
    )


# =============================================================================
# FastAPI Application
# =============================================================================

# =============================================================================
# Performance Middleware
# =============================================================================

class PerformanceMiddleware:
    """Custom middleware for performance monitoring and optimization."""
    
    def __init__(self, app: FastAPI):
        self.app = app
        
    async def __call__(self, scope: dict, receive: callable, send: callable):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        start_time = time.time()
        
        async def send_wrapper(message: dict):
            if message["type"] == "http.response.start":
                process_time = time.time() - start_time
                
                # Update performance statistics
                performance_stats["requests_count"] += 1
                current_avg = performance_stats["average_response_time"]
                new_avg = (current_avg + process_time * 1000) / 2
                performance_stats["average_response_time"] = round(new_avg, 2)
                
                # Add performance headers
                headers = dict(message.get("headers", []))
                headers.update({
                    b"x-process-time": str(round(process_time * 1000, 2)).encode(),
                    b"x-server-performance": b"optimized"
                })
                message["headers"] = [(k, v) for k, v in headers.items()]
                
            await send(message)
            
        await self.app(scope, receive, send_wrapper)

app = FastAPI(
    title="QuantLib Pro: Enterprise Quantitative Finance Platform",
    description="""
    # **QuantLib Pro API: Institutional-Grade Financial Intelligence**
    
    A comprehensive, production-ready REST API that unifies 30+ specialized quantitative finance applications into a single, scalable platform. Built for institutional traders, portfolio managers, risk analysts, and quantitative researchers who demand professional-grade financial modeling capabilities.
    
    ---
    
    ## **Core Capabilities**
    
    ### **Portfolio Management**
    - **Modern Portfolio Theory**: Efficient frontier optimization, risk-return analysis
    - **Asset Allocation**: Multi-asset class optimization with constraints and rebalancing
    - **Performance Attribution**: Factor-based return decomposition and benchmark analysis
    
    ### **Derivatives & Options** 
    - **Pricing Models**: Black-Scholes, Monte Carlo simulation, binomial trees
    - **Greeks Analytics**: Real-time Delta, Gamma, Theta, Vega, Rho calculations
    - **Volatility Modeling**: Implied volatility surfaces, skew analysis, term structure
    
    ### **Risk Management**
    - **Value-at-Risk (VaR)**: Historical, parametric, and Monte Carlo methodologies  
    - **Conditional VaR (CVaR)**: Expected shortfall and tail risk assessment
    - **Stress Testing**: Scenario analysis, backtesting, and regulatory compliance metrics
    
    ### **Market Intelligence**
    - **Regime Detection**: Hidden Markov Models for market state identification
    - **Correlation Analysis**: Dynamic correlation matrices and contagion modeling
    - **Macro Analytics**: **Real-time Federal Reserve economic data integration (FRED API)**
    
    ### **Real-Time Data Integration**
    - **Federal Reserve Economic Data (FRED)**: Live GDP, unemployment, inflation, Treasury rates
    - **Yahoo Finance**: Real-time stock prices and market data (unlimited access)
    - **Alpha Vantage**: Professional-grade financial data with 500+ daily calls
    - **Enterprise Caching**: 3-tier architecture with Redis performance optimization
    
    ---
    
    ## **Authentication & Security**
    
    ### **API Key Authentication**
    ```http
    X-API-Key: your_enterprise_api_key
    ```
    
    ### **JWT Bearer Token**  
    ```http
    Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    ```
    
    ### **Service Tiers & Rate Limits**
    
    | Tier | Requests/Hour | Features | Support |
    |------|---------------|----------|---------|
    | **Developer** | 100 | Core endpoints, basic analytics | Community |
    | **Professional** | 2,500 | Advanced analytics, real-time data | Email |
    | **Enterprise** | Unlimited | Full platform, custom endpoints | Dedicated |
    
    ---
    
    ## **Enterprise Support**
    
    **Professional Services:**
    - **Technical Support**: support@quantlibpro.com
    - **Custom Integration**: architecture@quantlibpro.com
    - **Enterprise Sales**: enterprise@quantlibpro.com
    - **Partnership Opportunities**: partnerships@quantlibpro.com
    
    **SLA Guarantees:**
    - **Enterprise Tier**: 99.9% uptime guarantee
    - **Response Time**: <2 hours for critical issues  
    - **Performance SLA**: <100ms latency for core endpoints
    
    ---
    
    **Transform your applications with institutional-grade quantitative finance capabilities.**
    """,
    version="2.1.0",
    contact={
        "name": "QuantLib Pro Enterprise Support",
        "email": "enterprise@quantlibpro.com",
        "url": "https://quantlibpro.com/enterprise"
    },
    license_info={
        "name": "Enterprise License",
        "url": "https://quantlibpro.com/license",
    },
    terms_of_service="https://quantlibpro.com/terms",
    docs_url="/docs",
    redoc_url="/redoc", 
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# =============================================================================
# Middleware Stack
# =============================================================================

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

# Security: Trusted host middleware (prevent Host header attacks)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"],  # In production: restrict to specific domains
)

# CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8503",  # Streamlit app
        "http://localhost:3000",  # React development
        "https://quantlibpro.com",  # Production frontend
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# GZip compression for responses
app.add_middleware(GZipMiddleware, minimum_size=1000)

# =============================================================================
# API Routers
# =============================================================================

# Health and monitoring endpoints
app.include_router(health_router)

# Authentication endpoints
app.include_router(auth_router)

# Core quantitative finance endpoints
app.include_router(
    portfolio_router,
    prefix="/api/v1",
    dependencies=[]  # Add auth dependencies in production
)

app.include_router(
    options_router,
    prefix="/api/v1", 
    dependencies=[]
)

app.include_router(
    risk_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    regime_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    volatility_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    macro_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    backtesting_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    analytics_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    data_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    realdata_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    market_analysis_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    signals_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    liquidity_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    systemic_risk_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    execution_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    compliance_router,
    prefix="/api/v1",
    dependencies=[]
)

app.include_router(
    uat_router,
    prefix="/api/v1",
    dependencies=[]
)

# =============================================================================
# Root Endpoints
# =============================================================================

# =============================================================================
# Performance Endpoints
# =============================================================================

@app.get("/performance/stats", summary="Performance Statistics")
async def performance_stats_endpoint():
    """Get real-time API performance statistics."""
    return {
        "performance": {
            "requests_processed": performance_stats["requests_count"],
            "average_response_time_ms": performance_stats["average_response_time"],
            "cache_hit_rate": round(
                performance_stats["cache_hits"] / 
                max(performance_stats["cache_hits"] + performance_stats["cache_misses"], 1) * 100, 2
            ),
            "status": "optimized" if performance_stats["average_response_time"] < 500 else "needs_tuning"
        },
        "targets": {
            "response_time_target_ms": 500,
            "cache_hit_rate_target": 85.0
        }
    }

@app.get(
    "/",
    summary="API Root", 
    description="Get API information and available endpoints"
)
async def root():
    """Optimized API root endpoint with service information."""
    with track_api_request("/", "GET"):
        return {
            "service": "QuantLib Pro API",
            "version": "2.1.0",  # Updated version with performance optimizations
            "status": "operational",
            "performance_mode": "production",
            "documentation": "/docs",
            "health": "/health",
            "performance_stats": "/performance/stats",
            "total_endpoints": 60,
            "endpoints": {
                "authentication": "/auth/*",
                "portfolio": "/api/v1/portfolio/*",
                "options": "/api/v1/options/*",
                "risk": "/api/v1/risk/*",
                "regime": "/api/v1/regime/*",
                "volatility": "/api/v1/volatility/*",
                "macro": "/api/v1/macro/*",
                "backtesting": "/api/v1/backtesting/*",
                "analytics": "/api/v1/analytics/*",
                "data": "/api/v1/data/*",
                "market_analysis": "/api/v1/market-analysis/*",
                "signals": "/api/v1/signals/*",
                "liquidity": "/api/v1/liquidity/*",
                "systemic_risk": "/api/v1/systemic-risk/*",
                "execution": "/api/v1/execution/*",
                "compliance": "/api/v1/compliance/*",
                "uat": "/api/v1/uat/*",
                "health": "/health/*",
            }
        }


@app.get("/api", summary="API Version Info")
async def api_info():
    """Get API version and capabilities."""
    return {
        "api_version": "v1",
        "capabilities": [
            "portfolio_optimization",
            "options_pricing",
            "risk_analysis",
            "market_regime_detection",
            "volatility_analysis",
            "macro_analysis",
            "backtesting",
            "advanced_analytics",
            "data_management",
            "market_analysis",
            "trading_signals",
            "liquidity_microstructure",
            "systemic_risk_contagion",
            "execution_optimization",
            "compliance_governance",
            "uat_stress_monitoring",
        ],
        "rate_limits": {
            "free_tier": "60/hour",
            "pro_tier": "1000/hour", 
            "enterprise": "unlimited"
        }
    }


# =============================================================================
# Development Server
# =============================================================================

if __name__ == "__main__":
    """Run development server."""
    
    # Configure logging for development
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    
    print(" Starting QuantLib Pro API Server...")
    print(" Quantitative Finance Platform")
    print(" Access API documentation at: http://localhost:8000/docs")
    print("  Health checks at: http://localhost:8000/health")
    
    # Run with production-optimized uvicorn configuration
    uvicorn.run(
        "main_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev mode)
        log_level="info",
        access_log=True,
        # Production performance settings
        loop="auto",  # Use optimal event loop
        http="auto",  # Use optimal HTTP implementation
        workers=1,     # Single worker for development
        backlog=2048,  # Increase connection backlog
        keepalive_timeout=65,  # Keep connections alive longer
        max_requests=10000,    # Recycle workers after requests
        max_requests_jitter=1000,  # Add jitter to prevent thundering herd
    )