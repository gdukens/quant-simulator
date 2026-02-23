"""Security: authentication, encryption, and rate limiting."""

from quantlib_pro.security.authentication import (
    AuthContext,
    AuthenticationError,
    AuthorizationError,
    Role,
    create_token,
    has_permission,
    require_permission,
    verify_token,
)
from quantlib_pro.security.encryption import (
    EncryptionError,
    decrypt,
    decrypt_str,
    encrypt,
    generate_key_hex,
    generate_salt_hex,
)
from quantlib_pro.security.rate_limiting import (
    InMemoryRateLimiter,
    RateLimitError,
    RedisRateLimiter,
    Tier,
    get_default_limiter,
    rate_limit,
)

__all__ = [
    # auth
    "AuthContext", "AuthenticationError", "AuthorizationError",
    "Role", "create_token", "verify_token", "has_permission", "require_permission",
    # encryption
    "EncryptionError", "encrypt", "decrypt", "decrypt_str",
    "generate_key_hex", "generate_salt_hex",
    # rate limiting
    "InMemoryRateLimiter", "RedisRateLimiter", "RateLimitError",
    "Tier", "rate_limit", "get_default_limiter",
]
