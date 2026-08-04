"""In-memory + optional JSONL analytics for parse jobs."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ParseMetric:
    parser_id: str
    source_file: str
    success: bool
    parse_time_ms: float
    record_count: int
    cache_hit: bool = False
    throughput_records_per_s: float = 0.0
    error_count: int = 0
    ts: float = field(default_factory=time.time)


class MetricsStore:
    def __init__(self, jsonl_path: Path | None = None) -> None:
        self._lock = threading.Lock()
        self._events: list[ParseMetric] = []
        self.jsonl_path = jsonl_path

    def record(self, metric: ParseMetric) -> None:
        with self._lock:
            self._events.append(metric)
            if self.jsonl_path is not None:
                try:
                    self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
                    with self.jsonl_path.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(asdict(metric), default=str) + "\n")
                except OSError:
                    pass

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            events = list(self._events)
        if not events:
            return {
                "count": 0,
                "success_rate": 0.0,
                "avg_parse_time_ms": 0.0,
                "total_records": 0,
                "cache_hit_rate": 0.0,
            }
        ok = sum(1 for e in events if e.success)
        hits = sum(1 for e in events if e.cache_hit)
        return {
            "count": len(events),
            "success_rate": ok / len(events),
            "avg_parse_time_ms": sum(e.parse_time_ms for e in events) / len(events),
            "total_records": sum(e.record_count for e in events),
            "cache_hit_rate": hits / len(events),
            "by_parser": self._by_parser(events),
        }

    def _by_parser(self, events: list[ParseMetric]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for e in events:
            bucket = out.setdefault(e.parser_id, {"count": 0, "records": 0, "failures": 0})
            bucket["count"] += 1
            bucket["records"] += e.record_count
            if not e.success:
                bucket["failures"] += 1
        return out
