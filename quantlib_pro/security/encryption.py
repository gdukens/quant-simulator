"""
Symmetric encryption for sensitive data at rest.

Uses Fernet (AES-128-CBC + HMAC-SHA256) from the ``cryptography`` package.
Key derivation follows PBKDF2-HMAC-SHA256 with a configurable iteration count.

Environment variables
---------------------
QUANTLIB_MASTER_KEY   Hex-encoded 32-byte master key.  If absent, a random
                      ephemeral key is generated (development mode).
QUANTLIB_SALT         Hex-encoded 16-byte salt for PBKDF2.
"""

from __future__ import annotations

import base64
import logging
import os
from functools import lru_cache

log = logging.getLogger(__name__)

_MASTER_KEY_ENV = "QUANTLIB_MASTER_KEY"
_SALT_ENV = "QUANTLIB_SALT"
_PBKDF2_ITERATIONS = 390_000       # OWASP 2023 recommendation


class EncryptionError(RuntimeError):
    pass


# ─── Key management ───────────────────────────────────────────────────────────

@lru_cache(maxsize=None)
def _get_fernet():
    """Return a Fernet instance, derived from the master key via PBKDF2."""
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        from cryptography.hazmat.primitives import hashes
    except ImportError as exc:
        raise EncryptionError(
            "Install 'cryptography' to enable encryption: pip install cryptography"
        ) from exc

    raw_key_hex = os.environ.get(_MASTER_KEY_ENV, "")
    salt_hex = os.environ.get(_SALT_ENV, "")

    if raw_key_hex:
        try:
            password = bytes.fromhex(raw_key_hex)
        except ValueError as exc:
            raise EncryptionError(
                f"{_MASTER_KEY_ENV} must be a hex-encoded string"
            ) from exc
    else:
        password = os.urandom(32)
        log.warning(
            "No %s set — using ephemeral encryption key. "
            "Data encrypted now cannot be decrypted after restart.",
            _MASTER_KEY_ENV,
        )

    if salt_hex:
        try:
            salt = bytes.fromhex(salt_hex)
        except ValueError as exc:
            raise EncryptionError(f"{_SALT_ENV} must be a hex-encoded string") from exc
    else:
        salt = b"quantlibpro_dev_"    # 16 bytes — deterministic for dev

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_PBKDF2_ITERATIONS,
    )
    derived = base64.urlsafe_b64encode(kdf.derive(password))
    return Fernet(derived)


# ─── Public API ───────────────────────────────────────────────────────────────

def encrypt(plaintext: str | bytes) -> bytes:
    """Encrypt *plaintext* and return ciphertext bytes."""
    if isinstance(plaintext, str):
        plaintext = plaintext.encode()
    try:
        return _get_fernet().encrypt(plaintext)
    except Exception as exc:
        raise EncryptionError(f"Encryption failed: {exc}") from exc


def decrypt(ciphertext: bytes) -> bytes:
    """Decrypt *ciphertext* and return plaintext bytes."""
    try:
        return _get_fernet().decrypt(ciphertext)
    except Exception as exc:
        raise EncryptionError(f"Decryption failed — wrong key or corrupted data") from exc


def decrypt_str(ciphertext: bytes) -> str:
    """Decrypt *ciphertext* and decode as UTF-8 string."""
    return decrypt(ciphertext).decode()


def generate_key_hex() -> str:
    """
    Generate a cryptographically secure random 32-byte key as hex string.

    Print and store this in ``QUANTLIB_MASTER_KEY`` for production use.
    """
    return os.urandom(32).hex()


def generate_salt_hex() -> str:
    """Generate a fresh 16-byte salt as hex string for ``QUANTLIB_SALT``."""
    return os.urandom(16).hex()
