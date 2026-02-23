"""
Authentication and Role-Based Access Control (RBAC).

Provides:
  - JWT token creation / verification
  - User roles: VIEWER, ANALYST, TRADER, ADMIN
  - Permission guards via the @require_permission decorator
  - AuthContext dataclass (pass-through for API handlers)

JWT is signed with HMAC-SHA256.  The secret is read from the
``QUANTLIB_JWT_SECRET`` environment variable; if absent a temporary
random key is generated (dev-safe, not prod-safe).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

log = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ─── Roles & permissions ──────────────────────────────────────────────────────

class Role(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    TRADER = "trader"
    ADMIN = "admin"


# Permission matrix: role → set of allowed actions
_PERMISSIONS: dict[Role, set[str]] = {
    Role.VIEWER: {"read:prices", "read:reports"},
    Role.ANALYST: {
        "read:prices", "read:reports",
        "compute:options", "compute:risk", "compute:portfolio",
    },
    Role.TRADER: {
        "read:prices", "read:reports",
        "compute:options", "compute:risk", "compute:portfolio",
        "execute:orders", "manage:portfolio",
    },
    Role.ADMIN: {"*"},  # wildcard — all permissions
}


def has_permission(role: Role, action: str) -> bool:
    perms = _PERMISSIONS.get(role, set())
    return "*" in perms or action in perms


# ─── JWT implementation (stdlib only, no PyJWT dependency) ────────────────────

_SECRET: bytes = os.environ.get("QUANTLIB_JWT_SECRET", "").encode() or os.urandom(32)
_ALGORITHM = "HS256"
_HEADER_B64 = urlsafe_b64encode(
    json.dumps({"alg": _ALGORITHM, "typ": "JWT"}).encode()
).rstrip(b"=")


def _b64_encode(data: bytes) -> bytes:
    return urlsafe_b64encode(data).rstrip(b"=")


def _b64_decode(data: str | bytes) -> bytes:
    if isinstance(data, str):
        data = data.encode()
    padding = 4 - len(data) % 4
    if padding != 4:
        data += b"=" * padding
    return urlsafe_b64decode(data)


def _sign(header_b64: bytes, payload_b64: bytes) -> bytes:
    msg = header_b64 + b"." + payload_b64
    return _b64_encode(hmac.new(_SECRET, msg, hashlib.sha256).digest())


def create_token(
    user_id: str,
    role: Role,
    ttl_seconds: int = 3600,
    extra_claims: Optional[dict] = None,
) -> str:
    """Return a signed JWT string."""
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role.value,
        "iat": now,
        "exp": now + ttl_seconds,
    }
    if extra_claims:
        payload.update(extra_claims)
    payload_b64 = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = _sign(_HEADER_B64, payload_b64)
    return f"{_HEADER_B64.decode()}.{payload_b64.decode()}.{sig.decode()}"


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify signature and expiry.  Returns the decoded payload dict.

    Raises
    ------
    AuthenticationError
        On any verification failure.
    """
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError as exc:
        raise AuthenticationError("Malformed token") from exc

    expected_sig = _sign(header_b64.encode(), payload_b64.encode())
    if not hmac.compare_digest(expected_sig, sig_b64.encode()):
        raise AuthenticationError("Invalid token signature")

    try:
        payload = json.loads(_b64_decode(payload_b64))
    except Exception as exc:
        raise AuthenticationError("Failed to decode token payload") from exc

    if payload.get("exp", 0) < int(time.time()):
        raise AuthenticationError("Token has expired")

    return payload


# ─── Exceptions ──────────────────────────────────────────────────────────────

class AuthenticationError(PermissionError):
    pass


class AuthorizationError(PermissionError):
    pass


# ─── Auth context ─────────────────────────────────────────────────────────────

@dataclass
class AuthContext:
    user_id: str
    role: Role
    issued_at: int
    expires_at: int
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_token(cls, token: str) -> "AuthContext":
        payload = verify_token(token)
        return cls(
            user_id=payload["sub"],
            role=Role(payload["role"]),
            issued_at=payload["iat"],
            expires_at=payload["exp"],
            extra={k: v for k, v in payload.items() if k not in ("sub", "role", "iat", "exp")},
        )

    def require_permission(self, action: str) -> None:
        if not has_permission(self.role, action):
            raise AuthorizationError(
                f"User '{self.user_id}' ({self.role.value}) lacks permission: '{action}'"
            )


# ─── Decorator ────────────────────────────────────────────────────────────────

def require_permission(action: str) -> Callable[[F], F]:
    """
    Decorator that validates ``auth_ctx`` keyword argument on the
    decorated function.

    Usage::

        @require_permission("compute:options")
        def price_option(S, K, T, r, sigma, *, auth_ctx: AuthContext):
            ...
    """
    def decorator(fn: F) -> F:
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            ctx: Optional[AuthContext] = kwargs.get("auth_ctx")
            if ctx is None:
                raise AuthenticationError(
                    f"Function '{fn.__name__}' requires 'auth_ctx' keyword argument"
                )
            ctx.require_permission(action)
            return fn(*args, **kwargs)
        return wrapper  # type: ignore[return-value]
    return decorator
