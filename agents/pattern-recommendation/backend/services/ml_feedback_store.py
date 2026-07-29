"""Persist operator accept/reject feedback for supervised retrain labels."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from backend.schemas.ml import MlFeedbackRequest, MlFeedbackResponse


class MlFeedbackStore:
    """Append-only JSONL feedback store under ml/data/."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = RLock()
        self._path = Path(settings.ml_feedback_path)

    def record(self, payload: MlFeedbackRequest) -> MlFeedbackResponse:
        recorded_at = datetime.now(timezone.utc)
        record = {
            "recorded_at": recorded_at.isoformat(),
            "domain": payload.domain,
            "pattern_id": payload.pattern_id,
            "decision": payload.decision,
            "note": payload.note,
            "metadata": payload.metadata,
        }
        with self._lock:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record) + "\n")
        get_logger().info(
            "ML feedback recorded domain=%s pattern=%s decision=%s",
            payload.domain,
            payload.pattern_id,
            payload.decision,
        )
        return MlFeedbackResponse(
            success=True,
            message="Feedback recorded",
            recorded_at=recorded_at,
        )

    def list_recent(self, limit: int = 50) -> list[dict]:
        if not self._path.exists():
            return []
        lines = self._path.read_text(encoding="utf-8").splitlines()
        rows: list[dict] = []
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return list(reversed(rows))


_feedback_store: MlFeedbackStore | None = None
_feedback_lock = RLock()


def get_ml_feedback_store(settings: Settings | None = None) -> MlFeedbackStore:
    global _feedback_store
    with _feedback_lock:
        if _feedback_store is None:
            _feedback_store = MlFeedbackStore(settings or get_settings())
        return _feedback_store


def reset_ml_feedback_store() -> None:
    global _feedback_store
    with _feedback_lock:
        _feedback_store = None
