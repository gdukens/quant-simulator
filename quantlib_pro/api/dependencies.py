"""
FastAPI dependencies for request handling, authentication, and common services.

Week 11: API Layer - Dependency injection for authentication, rate limiting,
                     and service access.
"""

import logging
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from quantlib_pro.observability import (
    check_health,
    get_performance_monitor,
    track_api_request,
)

logger = logging.getLogger(__name__)

# =============================================================================
# Security Dependencies
# =============================================================================

security = HTTPBearer(auto_error=False)


async def get_api_key(
    x_api_key: Annotated[Optional[str], Header()] = None,
) -> Optional[str]:
    """Extract API key from header."""
    return x_api_key


async def verify_api_key(
    api_key: Annotated[Optional[str], Depends(get_api_key)],
) -> str:
    """
    Verify API key (simplified - in production use proper auth service).
    
    Raises:
        HTTPException: If API key is invalid or missing.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In production: validate against database/cache
    # For now: simple validation
    if len(api_key) < 32:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    
    return api_key


async def get_current_user(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(security),
    ] = None,
) -> Optional[str]:
    """
    Get current user from Bearer token.
    
    In production, decode JWT and return user object.
    For now, returns simplified user ID.
    """
    if not credentials:
        return None
    
    # In production: decode JWT, validate, return user object
    token = credentials.credentials
    if not token:
        return None
    
    # Simplified: return token as user_id
    return f"user_{token[:8]}"


async def require_authentication(
    user: Annotated[Optional[str], Depends(get_current_user)],
) -> str:
    """
    Require authentication for endpoint.
    
    Raises:
        HTTPException: If not authenticated.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


# =============================================================================
# Rate Limiting Dependencies
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter.
    
    In production: use Redis-backed rate limiter like slowapi.
    """
    
    def __init__(self, requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests: Max requests per window
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self._requests: dict[str, list[datetime]] = {}
    
    def _clean_old_requests(self, client_id: str) -> None:
        """Remove requests outside current window."""
        if client_id not in self._requests:
            return
        
        cutoff = datetime.utcnow() - timedelta(seconds=self.window)
        self._requests[client_id] = [
            req_time for req_time in self._requests[client_id]
            if req_time > cutoff
        ]
    
    def is_allowed(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        self._clean_old_requests(client_id)
        
        if client_id not in self._requests:
            self._requests[client_id] = []
        
        if len(self._requests[client_id]) >= self.requests:
            return False
        
        self._requests[client_id].append(datetime.utcnow())
        return True
    
    def get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client."""
        self._clean_old_requests(client_id)
        
        if client_id not in self._requests:
            return self.requests
        
        return max(0, self.requests - len(self._requests[client_id]))


# Global rate limiter instance
_rate_limiter = RateLimiter(requests=100, window=60)


async def check_rate_limit(
    request: Request,
    api_key: Annotated[Optional[str], Depends(get_api_key)] = None,
) -> None:
    """
    Check rate limit for request.
    
    Raises:
        HTTPException: If rate limit exceeded.
    """
    # Use API key or IP as client identifier
    client_id = api_key if api_key else request.client.host
    
    if not _rate_limiter.is_allowed(client_id):
        remaining = _rate_limiter.get_remaining(client_id)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": str(_rate_limiter.requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(_rate_limiter.window),
            },
        )


# =============================================================================
# Service Dependencies
# =============================================================================

@lru_cache()
def get_settings():
    """
    Get application settings (cached).
    
    In production: load from environment variables or config service.
    """
    return {
        "app_name": "QuantLib Pro API",
        "version": "1.0.0",
        "environment": "development",
        "max_request_size": 10 * 1024 * 1024,  # 10 MB
        "default_page_size": 50,
        "max_page_size": 1000,
    }


async def get_db():
    """
    Get database connection (placeholder).
    
    In production: yield database session from connection pool.
    """
    # Placeholder for database dependency
    # In production:
    # try:
    #     db = SessionLocal()
    #     yield db
    # finally:
    #     db.close()
    
    yield None


async def get_cache():
    """
    Get cache connection (placeholder).
    
    In production: yield Redis connection from pool.
    """
    # Placeholder for cache dependency
    # In production:
    # try:
    #     cache = redis.Redis(...)
    #     yield cache
    # finally:
    #     cache.close()
    
    yield None


# =============================================================================
# Request Tracking Dependencies
# =============================================================================

async def track_request(
    request: Request,
) -> None:
    """
    Track API request for monitoring.
    
    Integrates with observability layer to track request metrics.
    """
    endpoint = request.url.path
    method = request.method
    
    # Track in performance monitor
    monitor = get_performance_monitor()
    monitor.record(
        name=f"{method} {endpoint}",
        duration=0.0,  # Will be updated by middleware
        error=False,
    )


# =============================================================================
# Pagination Dependencies
# =============================================================================

async def get_pagination(
    skip: int = 0,
    limit: int = 50,
    settings: dict = Depends(get_settings),
) -> dict[str, int]:
    """
    Get pagination parameters.
    
    Args:
        skip: Number of records to skip
        limit: Max number of records to return
        settings: Application settings
    
    Returns:
        Dictionary with skip and limit values
    
    Raises:
        HTTPException: If pagination parameters invalid
    """
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip must be non-negative",
        )
    
    max_limit = settings["max_page_size"]
    if limit < 1 or limit > max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit must be between 1 and {max_limit}",
        )
    
    return {"skip": skip, "limit": limit}


# =============================================================================
# Health Check Dependencies
# =============================================================================

async def verify_system_health() -> bool:
    """
    Verify system health before processing requests.
    
    Returns:
        True if system is healthy
    
    Raises:
        HTTPException: If system is unhealthy
    """
    health = check_health()
    
    if health.overall_status.name == "UNHEALTHY":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is unhealthy",
        )
    
    return True


# =============================================================================
# Input Validation Dependencies
# =============================================================================

async def validate_date_range(
    start_date: str,
    end_date: str,
) -> tuple[str, str]:
    """
    Validate date range.
    
    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Validated date range
    
    Raises:
        HTTPException: If date range is invalid
    """
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {e}",
        )
    
    if start >= end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date",
        )
    
    # Check date range is not too large (e.g., max 10 years)
    max_days = 365 * 10
    if (end - start).days > max_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Date range too large (max {max_days} days)",
        )
    
    return start_date, end_date


async def validate_tickers(
    tickers: list[str],
    max_tickers: int = 50,
) -> list[str]:
    """
    Validate ticker list.
    
    Args:
        tickers: List of ticker symbols
        max_tickers: Maximum number of tickers allowed
    
    Returns:
        Validated ticker list
    
    Raises:
        HTTPException: If tickers are invalid
    """
    if not tickers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one ticker required",
        )
    
    if len(tickers) > max_tickers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {max_tickers} tickers allowed",
        )
    
    # Validate ticker format (simple check)
    for ticker in tickers:
        if not ticker or not ticker.replace(".", "").replace("-", "").isalnum():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid ticker format: {ticker}",
            )
    
    return tickers
