"""
PA-UX-003 — Analysis Job Progress Framework (observability only).

In-memory Progress Manager. Never writes disk. Never controls the pipeline.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional

from session_perf_trace import SESSION_PERF_TRACE_JSON

# Bound only for the Validate worker thread that opted into progress.
_bound_job_id: ContextVar[Optional[str]] = ContextVar("paa_progress_job_id", default=None)

JOB_TTL_SECONDS = 45.0
STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_phase_weights_from_perf_trace(output_dir: str) -> Optional[Dict[str, float]]:
    """
    Read-only advisory weights from the last L2 perf trace.
    Returns None when history is missing or unusable (UI shows Estimating...).
    """
    path = os.path.join(output_dir, SESSION_PERF_TRACE_JSON)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except Exception:
        return None
    phases = payload.get("phases") if isinstance(payload, dict) else None
    if not isinstance(phases, list) or not phases:
        return None
    totals: Dict[str, float] = {}
    for row in phases:
        if not isinstance(row, dict):
            continue
        name = row.get("name")
        if not name:
            continue
        try:
            wall = float(row.get("wall_ms") or 0.0)
        except (TypeError, ValueError):
            continue
        if wall <= 0:
            continue
        key = str(name)
        totals[key] = totals.get(key, 0.0) + wall
    total = sum(totals.values())
    if total <= 0:
        return None
    return {name: wall / total for name, wall in totals.items()}


@dataclass
class _JobState:
    job_id: str
    status: str = STATUS_QUEUED
    current_phase: Optional[str] = None
    completed_phases: List[str] = field(default_factory=list)
    percentage: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None
    started_at: str = field(default_factory=_utc_now_iso)
    finished_at: Optional[str] = None
    error_phase: Optional[str] = None
    error_message: Optional[str] = None
    result: Any = None
    phase_weights: Optional[Dict[str, float]] = None
    t0: float = field(default_factory=time.perf_counter)
    cleanup_timer: Optional[threading.Timer] = None


class ProgressManager:
    """Thread-safe ephemeral progress store. Pipeline never waits on this."""

    def __init__(self, *, ttl_seconds: float = JOB_TTL_SECONDS) -> None:
        self._lock = threading.Lock()
        self._jobs: Dict[str, _JobState] = {}
        self._ttl_seconds = float(ttl_seconds)

    def create_job(
        self,
        *,
        phase_weights: Optional[Dict[str, float]] = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        state = _JobState(job_id=job_id, phase_weights=phase_weights)
        with self._lock:
            self._jobs[job_id] = state
        return job_id

    def mark_running(self, job_id: str) -> None:
        with self._lock:
            state = self._jobs.get(job_id)
            if state is None:
                return
            if state.status in (STATUS_COMPLETED, STATUS_FAILED):
                return
            state.status = STATUS_RUNNING
            state.started_at = _utc_now_iso()
            state.t0 = time.perf_counter()

    def start_phase(self, job_id: str, name: str) -> None:
        # Hot path: atomic field updates only.
        with self._lock:
            state = self._jobs.get(job_id)
            if state is None or state.status in (STATUS_COMPLETED, STATUS_FAILED):
                return
            state.status = STATUS_RUNNING
            state.current_phase = name
            self._refresh_timing_locked(state)

    def finish_phase(self, job_id: str, name: str) -> None:
        with self._lock:
            state = self._jobs.get(job_id)
            if state is None or state.status in (STATUS_COMPLETED, STATUS_FAILED):
                return
            state.completed_phases.append(name)
            if state.current_phase == name:
                state.current_phase = None
            self._recompute_percentage_locked(state)
            self._refresh_timing_locked(state)

    def complete(self, job_id: str, result: Any) -> None:
        with self._lock:
            state = self._jobs.get(job_id)
            if state is None:
                return
            state.status = STATUS_COMPLETED
            state.current_phase = None
            state.percentage = 100.0
            state.estimated_remaining_seconds = 0.0
            state.finished_at = _utc_now_iso()
            state.result = result
            self._refresh_timing_locked(state)
            self._schedule_cleanup_locked(job_id, state)

    def fail(self, job_id: str, message: str, *, phase: Optional[str] = None) -> None:
        with self._lock:
            state = self._jobs.get(job_id)
            if state is None:
                return
            state.status = STATUS_FAILED
            state.error_phase = phase or state.current_phase
            state.error_message = (message or "Validation failed").strip()[:200]
            state.current_phase = state.error_phase
            state.finished_at = _utc_now_iso()
            state.estimated_remaining_seconds = None
            self._refresh_timing_locked(state)
            self._schedule_cleanup_locked(job_id, state)

    def snapshot(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            state = self._jobs.get(job_id)
            if state is None:
                return None
            self._refresh_timing_locked(state)
            return {
                "job_id": state.job_id,
                "status": state.status,
                "current_phase": state.current_phase,
                "completed_phases": list(state.completed_phases),
                "percentage": state.percentage,
                "elapsed_seconds": round(time.perf_counter() - state.t0, 1),
                "estimated_remaining_seconds": (
                    None
                    if state.estimated_remaining_seconds is None
                    else round(float(state.estimated_remaining_seconds), 1)
                ),
                "started_at": state.started_at,
                "finished_at": state.finished_at,
                "error_phase": state.error_phase,
                "error_message": state.error_message,
            }

    def get_result(self, job_id: str) -> Optional[_JobState]:
        with self._lock:
            return self._jobs.get(job_id)

    def discard(self, job_id: str) -> None:
        with self._lock:
            state = self._jobs.pop(job_id, None)
            if state and state.cleanup_timer is not None:
                state.cleanup_timer.cancel()

    def _recompute_percentage_locked(self, state: _JobState) -> None:
        weights = state.phase_weights
        if not weights:
            state.percentage = None
            state.estimated_remaining_seconds = None
            return
        done = 0.0
        for name in state.completed_phases:
            done += float(weights.get(name, 0.0))
        # Cap below 100 until complete(); unknown phases add 0 weight.
        state.percentage = round(min(99.0, max(0.0, done * 100.0)), 1)
        self._refresh_timing_locked(state)

    def _refresh_timing_locked(self, state: _JobState) -> None:
        elapsed = time.perf_counter() - state.t0
        if state.status == STATUS_COMPLETED:
            state.estimated_remaining_seconds = 0.0
            return
        if state.status == STATUS_FAILED:
            state.estimated_remaining_seconds = None
            return
        pct = state.percentage
        weights = state.phase_weights
        if pct is None or weights is None or pct <= 0:
            state.estimated_remaining_seconds = None
            return
        # remaining ≈ elapsed * (1 - p) / p
        remaining_frac = max(0.0, 1.0 - (pct / 100.0))
        done_frac = pct / 100.0
        if done_frac <= 0:
            state.estimated_remaining_seconds = None
            return
        state.estimated_remaining_seconds = elapsed * remaining_frac / done_frac

    def _schedule_cleanup_locked(self, job_id: str, state: _JobState) -> None:
        if state.cleanup_timer is not None:
            state.cleanup_timer.cancel()

        def _cleanup() -> None:
            self.discard(job_id)

        timer = threading.Timer(self._ttl_seconds, _cleanup)
        timer.daemon = True
        state.cleanup_timer = timer
        timer.start()


# Process-wide manager (ephemeral).
progress_manager = ProgressManager()


def bind_progress_job(job_id: str) -> Token:
    return _bound_job_id.set(job_id)


def unbind_progress_job(token: Token) -> None:
    _bound_job_id.reset(token)


def current_progress_job_id() -> Optional[str]:
    return _bound_job_id.get()


def notify_phase_start(name: str) -> None:
    """Called from SessionPerfTrace only. Never raises to the pipeline."""
    job_id = _bound_job_id.get()
    if job_id is None:
        return
    try:
        progress_manager.start_phase(job_id, name)
    except Exception:
        pass


def notify_phase_finish(name: str) -> None:
    job_id = _bound_job_id.get()
    if job_id is None:
        return
    try:
        progress_manager.finish_phase(job_id, name)
    except Exception:
        pass


@contextmanager
def progress_job_context(job_id: str) -> Iterator[None]:
    token = bind_progress_job(job_id)
    try:
        yield
    finally:
        unbind_progress_job(token)


def install_session_perf_trace_hooks() -> None:
    """Subscribe ProgressManager to SessionPerfTrace (idempotent)."""
    import session_perf_trace as spt

    spt.on_phase_start = notify_phase_start
    spt.on_phase_finish = notify_phase_finish
