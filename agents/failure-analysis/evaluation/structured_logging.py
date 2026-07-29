"""Structured logging for evaluation executions."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvaluationLogger:
    """Structured JSON-line logger with execution / correlation IDs."""

    def __init__(
        self,
        *,
        log_dir: Path | str,
        level: str = "INFO",
        execution_id: str | None = None,
        correlation_id: str | None = None,
        dataset_name: str = "",
    ) -> None:
        self.execution_id = execution_id or str(uuid.uuid4())
        self.correlation_id = correlation_id or self.execution_id
        self.dataset_name = dataset_name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / f"execution_{self.execution_id}.jsonl"
        self._logger = logging.getLogger(f"evaluation.{self.execution_id}")
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            )
            self._logger.addHandler(handler)

    def log(
        self,
        *,
        module: str,
        status: str,
        duration_ms: float = 0.0,
        message: str = "",
        exception: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "execution_id": self.execution_id,
            "correlation_id": self.correlation_id,
            "dataset_name": self.dataset_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "module": module,
            "status": status,
            "duration_ms": duration_ms,
            "message": message,
            "exception": exception,
            "extra": extra or {},
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str) + "\n")
        level = logging.ERROR if status == "FAIL" else logging.INFO
        self._logger.log(
            level,
            "[%s] %s status=%s duration_ms=%.2f %s",
            module,
            self.dataset_name or "-",
            status,
            duration_ms,
            message,
        )
        return record

    def history(self, *, limit: int = 200) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        rows: list[dict[str, Any]] = []
        with self.log_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows[-limit:]
