"""
Health check endpoints for Kubernetes and monitoring.

Week 11: API Layer - Health endpoints integrating with observability layer.
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Response, status

from quantlib_pro.observability import (
    HealthStatus,
    check_health,
    export_metrics,
    get_metrics_snapshot,
    liveness_probe,
    readiness_probe,
)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", summary="Basic health check")
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.
    
    Returns OK status if the application is running.
    Used by load balancers for basic health monitoring.
    
    Returns:
        Dictionary with status and timestamp
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "quantlib-pro-api",
    }


@router.get("/live", summary="Liveness probe")
async def liveness() -> Dict[str, Any]:
    """
    Kubernetes liveness probe.
    
    Checks if the application is alive and should not be restarted.
    This endpoint should only fail if the application is completely broken.
    
    Returns:
        Dictionary with liveness status
    """
    is_alive = liveness_probe()
    
    return {
        "alive": is_alive,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready", summary="Readiness probe")
async def readiness(response: Response) -> Dict[str, Any]:
    """
    Kubernetes readiness probe.
    
    Checks if the application is ready to serve traffic.
    This endpoint should fail if dependencies are unhealthy
    or the service is in a degraded state.
    
    Args:
        response: FastAPI response object to set status code
    
    Returns:
        Dictionary with readiness status
    """
    is_ready = readiness_probe()
    
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "ready": is_ready,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/detailed", summary="Detailed health check")
async def detailed_health() -> Dict[str, Any]:
    """
    Detailed health check with component status.
    
    Provides comprehensive health information for all system components.
    Used by operations dashboards and monitoring systems.
    
    Returns:
        Dictionary with overall status and component details
    """
    health = check_health()
    
    # Convert health check results to API response format
    components = {}
    for result in health.checks:
        components[result.component] = {
            "status": result.status.name.lower(),
            "message": result.message,
            "latency_ms": result.latency_ms,
            "timestamp": result.timestamp.isoformat(),
        }
        
        if result.details:
            components[result.component]["details"] = result.details
    
    return {
        "overall_status": health.overall_status.name.lower(),
        "components": components,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "quantlib-pro-api",
    }


@router.get("/startup", summary="Startup probe")
async def startup(response: Response) -> Dict[str, Any]:
    """
    Kubernetes startup probe.
    
    Checks if the application has completed initialization.
    This endpoint should only return success once the application
    is fully initialized and ready for liveness/readiness checks.
    
    Args:
        response: FastAPI response object to set status code
    
    Returns:
        Dictionary with startup status
    """
    # Check if critical components are initialized
    health = check_health()
    
    # Consider app started if not UNKNOWN (UNKNOWN means not initialized)
    is_started = health.overall_status != HealthStatus.UNKNOWN
    
    if not is_started:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return {
        "started": is_started,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/metrics", summary="Prometheus metrics")
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus exposition format for scraping.
    
    Returns:
        Response with Prometheus-formatted metrics
    """
    metrics_data, content_type = export_metrics()
    
    return Response(
        content=metrics_data,
        media_type=content_type,
    )


@router.get("/metrics/snapshot", summary="Metrics snapshot")
async def metrics_snapshot() -> Dict[str, Any]:
    """
    Get current metrics snapshot in JSON format.
    
    Provides a JSON representation of current metrics for
    monitoring dashboards and debugging.
    
    Returns:
        Dictionary with current metrics
    """
    snapshot = get_metrics_snapshot()
    
    return {
        "metrics": {
            "calculations": snapshot.calculations_total,
            "errors": snapshot.errors_total,
            "cache_hit_rate": (
                snapshot.cache_hits / (snapshot.cache_hits + snapshot.cache_misses)
                if (snapshot.cache_hits + snapshot.cache_misses) > 0
                else 0.0
            ),
            "portfolio_count": snapshot.portfolio_count,
            "api_requests": snapshot.api_requests_total,
        },
        "timestamp": snapshot.timestamp.isoformat(),
    }


@router.get("/status", summary="Service status")
async def service_status() -> Dict[str, Any]:
    """
    Comprehensive service status endpoint.
    
    Combines health check and metrics for a complete service overview.
    
    Returns:
        Dictionary with service status, health, and key metrics
    """
    health = check_health()
    snapshot = get_metrics_snapshot()
    
    return {
        "service": "quantlib-pro-api",
        "version": "1.0.0",
        "status": health.overall_status.name.lower(),
        "health": {
            "overall": health.overall_status.name.lower(),
            "components": len(health.checks),
            "healthy": sum(
                1 for c in health.checks
                if c.status == HealthStatus.HEALTHY
            ),
            "degraded": sum(
                1 for c in health.checks
                if c.status == HealthStatus.DEGRADED
            ),
            "unhealthy": sum(
                1 for c in health.checks
                if c.status == HealthStatus.UNHEALTHY
            ),
        },
        "metrics": {
            "total_calculations": snapshot.calculations_total,
            "total_errors": snapshot.errors_total,
            "cache_hit_rate": (
                snapshot.cache_hits / (snapshot.cache_hits + snapshot.cache_misses)
                if (snapshot.cache_hits + snapshot.cache_misses) > 0
                else 0.0
            ),
            "total_api_requests": snapshot.api_requests_total,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
