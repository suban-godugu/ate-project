"""
Session performance trace — additive, non-fatal Layer 2 profiling.

Emits PA-Analysis-Session_perf_trace.json as a secondary artifact.
Never mutates Layer 1 engineering results.
"""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterator, List, Optional

from analysis_session import SESSION_GENERATED_BY

logger = logging.getLogger(__name__)

SESSION_PERF_TRACE_JSON = "PA-Analysis-Session_perf_trace.json"
PERF_TRACE_SCHEMA_VERSION = "1.0"

# PA-UX-003: optional phase observers (default None = identical Trace path).
# Progress framework may assign these; engineering never calls ProgressManager.
on_phase_start: Optional[Callable[[str], None]] = None
on_phase_finish: Optional[Callable[[str], None]] = None


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class SessionPerfTrace:
    """Collect phase wall times and per-artifact write telemetry."""

    def __init__(self) -> None:
        self.started_at_utc = _utc_now_iso()
        self.finished_at_utc: Optional[str] = None
        self._t0 = time.perf_counter()
        self.phases: List[Dict[str, Any]] = []
        self.writes: List[Dict[str, Any]] = []
        self.notes: List[str] = []
        self.session_hash: Optional[str] = None
        self._open_phases: Dict[str, float] = {}
        self._lock = threading.Lock()

    @contextmanager
    def phase(self, name: str) -> Iterator[None]:
        start = time.perf_counter()
        with self._lock:
            self._open_phases[name] = start
        # Passive observer (logging-style). Default hooks are None.
        start_cb = on_phase_start
        if start_cb is not None:
            try:
                start_cb(name)
            except Exception:
                pass
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            with self._lock:
                self._open_phases.pop(name, None)
                self.phases.append(
                    {
                        "name": name,
                        "wall_ms": round(elapsed_ms, 3),
                    }
                )
            finish_cb = on_phase_finish
            if finish_cb is not None:
                try:
                    finish_cb(name)
                except Exception:
                    pass

    def record_write(
        self,
        *,
        artifact: str,
        serialize_ms: float,
        nbytes: int,
    ) -> None:
        with self._lock:
            self.writes.append(
                {
                    "artifact": artifact,
                    "serialize_ms": round(float(serialize_ms), 3),
                    "bytes": int(nbytes),
                }
            )

    def add_note(self, note: str) -> None:
        text = str(note or "").strip()
        if text:
            with self._lock:
                self.notes.append(text)

    def finalize(self, *, session_hash: Optional[str] = None) -> Dict[str, Any]:
        self.finished_at_utc = _utc_now_iso()
        if session_hash is not None:
            self.session_hash = session_hash
        total_wall_ms = (time.perf_counter() - self._t0) * 1000.0
        with self._lock:
            phases_snapshot = list(self.phases)
            writes_snapshot = list(self.writes)
            notes_snapshot = list(self.notes)
        phases_out: List[Dict[str, Any]] = []
        for row in phases_snapshot:
            wall_ms = float(row.get("wall_ms") or 0.0)
            pct = (wall_ms / total_wall_ms * 100.0) if total_wall_ms > 0 else 0.0
            phases_out.append(
                {
                    "name": row.get("name"),
                    "wall_ms": wall_ms,
                    "pct_of_total": round(pct, 3),
                }
            )
        return {
            "generated_by": SESSION_GENERATED_BY,
            "artifact": "perf_trace",
            "schema_version": PERF_TRACE_SCHEMA_VERSION,
            "session_hash": self.session_hash,
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
            "total_wall_ms": round(total_wall_ms, 3),
            "phases": phases_out,
            "writes": writes_snapshot,
            "notes": notes_snapshot,
        }


@contextmanager
def optional_phase(trace: Optional[SessionPerfTrace], name: str) -> Iterator[None]:
    """Run a timed phase when a tracer is present; otherwise a no-op."""
    if trace is None:
        yield
        return
    with trace.phase(name):
        yield


def write_session_perf_trace(
    output_dir: str,
    trace: SessionPerfTrace,
    *,
    session_hash: Optional[str] = None,
) -> Optional[str]:
    """
    Persist perf trace JSON. Returns path on success, None on failure.

    Failures are logged and never raised to the caller.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, SESSION_PERF_TRACE_JSON)
        payload = trace.finalize(session_hash=session_hash)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        return path
    except Exception:
        logger.exception(
            "Analysis Session perf trace write failed; "
            "core Analysis Session artifacts remain available."
        )
        return None
