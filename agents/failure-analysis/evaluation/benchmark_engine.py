"""Performance benchmarking and resource monitoring."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class BenchmarkSample:
    name: str
    duration_ms: float
    cpu_percent: float | None = None
    memory_mb: float | None = None
    disk_used_mb: float | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "duration_ms": self.duration_ms,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "disk_used_mb": self.disk_used_mb,
            "extra": self.extra,
        }


class ResourceMonitor:
    """Optional psutil-backed resource snapshot (graceful without psutil)."""

    def snapshot(self, path: str | None = None) -> dict[str, float | None]:
        try:
            import psutil
        except ImportError:
            return {"cpu_percent": None, "memory_mb": None, "disk_used_mb": None}

        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = psutil.cpu_percent(interval=0.05)
        disk_used_mb = None
        if path:
            try:
                usage = psutil.disk_usage(path)
                disk_used_mb = usage.used / (1024 * 1024)
            except OSError:
                disk_used_mb = None
        return {
            "cpu_percent": float(cpu_percent),
            "memory_mb": round(float(memory_mb), 3),
            "disk_used_mb": None if disk_used_mb is None else round(float(disk_used_mb), 3),
        }


class BenchmarkEngine:
    """Measure timed stages and accumulate historical benchmark samples."""

    def __init__(self) -> None:
        self.monitor = ResourceMonitor()
        self.samples: list[BenchmarkSample] = []
        self._history: list[dict[str, Any]] = []

    def measure(
        self,
        name: str,
        fn: Callable[[], Any],
        *,
        disk_path: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> tuple[Any, BenchmarkSample]:
        before = self.monitor.snapshot(disk_path)
        start = time.perf_counter()
        result = fn()
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        after = self.monitor.snapshot(disk_path)
        sample = BenchmarkSample(
            name=name,
            duration_ms=duration_ms,
            cpu_percent=after.get("cpu_percent"),
            memory_mb=after.get("memory_mb"),
            disk_used_mb=after.get("disk_used_mb"),
            extra={
                **(extra or {}),
                "memory_delta_mb": _delta(before.get("memory_mb"), after.get("memory_mb")),
            },
        )
        self.samples.append(sample)
        return result, sample

    def summarize(
        self,
        *,
        targets_ms: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        targets_ms = targets_ms or {}
        by_name: dict[str, list[BenchmarkSample]] = {}
        for sample in self.samples:
            by_name.setdefault(sample.name, []).append(sample)

        stages: list[dict[str, Any]] = []
        for name, items in by_name.items():
            avg_ms = sum(i.duration_ms for i in items) / len(items)
            target = targets_ms.get(name)
            stages.append(
                {
                    "name": name,
                    "count": len(items),
                    "avg_ms": round(avg_ms, 3),
                    "max_ms": round(max(i.duration_ms for i in items), 3),
                    "min_ms": round(min(i.duration_ms for i in items), 3),
                    "target_ms": target,
                    "meets_target": True if target is None else avg_ms <= target,
                    "cpu_percent": items[-1].cpu_percent,
                    "memory_mb": items[-1].memory_mb,
                }
            )

        summary = {
            "stage_count": len(stages),
            "total_measured_ms": round(sum(s.duration_ms for s in self.samples), 3),
            "stages": stages,
            "samples": [s.to_dict() for s in self.samples],
        }
        self._history.append(summary)
        return summary

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)


def _delta(before: float | None, after: float | None) -> float | None:
    if before is None or after is None:
        return None
    return round(after - before, 3)
