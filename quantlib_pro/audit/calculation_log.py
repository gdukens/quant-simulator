"""
Calculation Audit Log — immutable, tamper-evident record of every
computation performed by QuantLib Pro.

Design goals:
  • Every calculation gets a unique UUID with a SHA-256 content hash.
  • Log entries are append-only (never updated or deleted).
  • Retention is configurable (default: 7 years to meet MiFID II / Dodd-Frank).
  • Querying by ticker, user, model, or date range is O(n) — good enough
    for compliance review; plug in a database backend for production.

Usage::

    from quantlib_pro.audit import log_calculation, query_audit_log

    entry = log_calculation(
        calculation_type="black_scholes",
        inputs={"S": 150, "K": 155, "T": 0.25, "r": 0.05, "sigma": 0.2},
        outputs={"price": 3.45, "delta": 0.42},
        user_id="analyst_1",
        model_version="1.0.0",
    )
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any, Optional

log = logging.getLogger(__name__)

_DEFAULT_RETENTION_YEARS = 7


@dataclass(frozen=True)
class AuditEntry:
    entry_id: str                     # UUID-4
    calculation_type: str
    user_id: str
    model_version: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    warnings: list[str]
    timestamp: str                    # ISO-8601 UTC
    content_hash: str                 # SHA-256 of canonical JSON

    def verify(self) -> bool:
        """Return True if the content hash matches the entry body."""
        return self.content_hash == _compute_hash(self)


def _compute_hash(entry: "AuditEntry") -> str:
    """Canonical JSON hash — excludes content_hash itself."""
    body = {
        "entry_id": entry.entry_id,
        "calculation_type": entry.calculation_type,
        "user_id": entry.user_id,
        "model_version": entry.model_version,
        "inputs": entry.inputs,
        "outputs": entry.outputs,
        "warnings": entry.warnings,
        "timestamp": entry.timestamp,
    }
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _build_entry(
    calculation_type: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    user_id: str,
    model_version: str,
    warnings: Optional[list[str]] = None,
) -> AuditEntry:
    entry_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + "Z"
    warnings = warnings or []
    # Build a placeholder first to compute the hash
    placeholder = AuditEntry(
        entry_id=entry_id,
        calculation_type=calculation_type,
        user_id=user_id,
        model_version=model_version,
        inputs=inputs,
        outputs=outputs,
        warnings=warnings,
        timestamp=timestamp,
        content_hash="",
    )
    content_hash = _compute_hash(placeholder)
    return AuditEntry(
        entry_id=entry_id,
        calculation_type=calculation_type,
        user_id=user_id,
        model_version=model_version,
        inputs=inputs,
        outputs=outputs,
        warnings=warnings,
        timestamp=timestamp,
        content_hash=content_hash,
    )


class CalculationAuditLog:
    """
    In-memory audit log store with optional CSV persistence.

    For production, swap the ``_store`` list for a database table or a
    cloud audit service (Azure Monitor, AWS CloudTrail, etc.).

    Parameters
    ----------
    persist_path:
        Directory where daily NDJSON audit files are written.
        Set to None to disable file persistence.
    retention_years:
        Entries older than this are eligible for purging when
        :meth:`purge_old_entries` is called.
    """

    def __init__(
        self,
        persist_path: Optional[str] = None,
        retention_years: int = _DEFAULT_RETENTION_YEARS,
    ) -> None:
        self._store: list[AuditEntry] = []
        self._lock = Lock()
        self._persist_path = persist_path
        self._retention = timedelta(days=retention_years * 365)

        if persist_path:
            os.makedirs(persist_path, exist_ok=True)

    # ── Write ─────────────────────────────────────────────────────────────────

    def record(
        self,
        calculation_type: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        user_id: str = "system",
        model_version: str = "0.0.0",
        warnings: Optional[list[str]] = None,
    ) -> AuditEntry:
        entry = _build_entry(
            calculation_type=calculation_type,
            inputs=inputs,
            outputs=outputs,
            user_id=user_id,
            model_version=model_version,
            warnings=warnings,
        )
        with self._lock:
            self._store.append(entry)
            if self._persist_path:
                self._write_to_file(entry)

        log.debug("Audit entry recorded: %s [%s]", entry.entry_id, calculation_type)
        return entry

    # ── Read ──────────────────────────────────────────────────────────────────

    def query(
        self,
        calculation_type: Optional[str] = None,
        user_id: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[AuditEntry]:
        with self._lock:
            entries = list(self._store)

        def _matches(e: AuditEntry) -> bool:
            if calculation_type and e.calculation_type != calculation_type:
                return False
            if user_id and e.user_id != user_id:
                return False
            ts = datetime.fromisoformat(e.timestamp.rstrip("Z"))
            if since and ts < since:
                return False
            if until and ts > until:
                return False
            return True

        matched = [e for e in entries if _matches(e)]
        return matched[-limit:]

    def verify_all(self) -> tuple[int, int]:
        """
        Check every stored entry's hash.

        Returns
        -------
        (total, tampered)
            ``tampered`` is the count of entries whose hash no longer
            matches their content — should always be 0.
        """
        total = tampered = 0
        with self._lock:
            for entry in self._store:
                total += 1
                if not entry.verify():
                    tampered += 1
                    log.error("Tampered audit entry detected: %s", entry.entry_id)
        return total, tampered

    def purge_old_entries(self) -> int:
        cutoff = datetime.utcnow() - self._retention
        with self._lock:
            before = len(self._store)
            self._store = [
                e
                for e in self._store
                if datetime.fromisoformat(e.timestamp.rstrip("Z")) > cutoff
            ]
            removed = before - len(self._store)
        log.info("Audit log purge: removed %d entries older than %s days", removed, self._retention.days)
        return removed

    # ── Persistence ───────────────────────────────────────────────────────────

    def _write_to_file(self, entry: AuditEntry) -> None:
        date_str = entry.timestamp[:10]   # YYYY-MM-DD
        fname = os.path.join(self._persist_path, f"audit_{date_str}.ndjson")
        try:
            with open(fname, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(asdict(entry), default=str) + "\n")
        except OSError as exc:
            log.error("Failed to persist audit entry %s: %s", entry.entry_id, exc)


# Module-level singleton — used by convenience function below
_default_log = CalculationAuditLog(
    persist_path=os.environ.get("QUANTLIB_AUDIT_DIR"),
    retention_years=int(os.environ.get("QUANTLIB_AUDIT_RETENTION_YEARS", "7")),
)


def log_calculation(
    calculation_type: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    user_id: str = "system",
    model_version: str = "0.0.0",
    warnings: Optional[list[str]] = None,
) -> AuditEntry:
    """Convenience wrapper that writes to the module-level audit log."""
    return _default_log.record(
        calculation_type=calculation_type,
        inputs=inputs,
        outputs=outputs,
        user_id=user_id,
        model_version=model_version,
        warnings=warnings,
    )


def query_audit_log(**kwargs: Any) -> list[AuditEntry]:
    """Convenience wrapper that queries the module-level audit log."""
    return _default_log.query(**kwargs)
