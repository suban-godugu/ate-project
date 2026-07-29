"""Unified dataset loader with lazy caching and streaming support."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from threading import RLock
from typing import Any

import ijson

from backend.core.config import Settings, get_settings
from backend.core.exceptions import AppException
from backend.core.logging import get_logger
from backend.schemas.datasets import DatasetInfo
from backend.services.dataset_service import DatasetService, get_dataset_service


class DataLoader:
    """
    Single entry point for loading analysis datasets.

    Small datasets are loaded once and cached.
    Execution datasets are always streamed and never json.load()-ed.
    """

    def __init__(
        self,
        settings: Settings,
        dataset_service: DatasetService,
    ) -> None:
        self._settings = settings
        self._dataset_service = dataset_service
        self._lock = RLock()
        self._json_cache: dict[str, Any] = {}
        self._csv_cache: dict[str, list[dict[str, str]]] = {}
        self._stream_markers: set[str] = set()

    def clear_cache(self) -> None:
        """Drop all cached dataset payloads."""
        with self._lock:
            self._json_cache.clear()
            self._csv_cache.clear()
            self._stream_markers.clear()
        get_logger().info("DataLoader cache cleared")

    def invalidate_role(self, role: str) -> None:
        """Drop a single cached role so the next read reloads from disk."""
        with self._lock:
            self._json_cache.pop(role, None)
            self._csv_cache.pop(role, None)
            self._stream_markers.discard(role)
        get_logger().info("DataLoader cache invalidated role=%s", role)

    def resolve_dataset(self, role: str) -> DatasetInfo:
        """Resolve an available dataset for a logical role from the registry."""
        marker = self._settings.parsed_role_markers().get(role)
        if not marker:
            raise AppException(
                f"Unknown dataset role '{role}'",
                status_code=500,
                details={"role": role},
            )

        candidates = [
            item
            for item in self._dataset_service.get_datasets().datasets
            if item.status == "available"
            and marker in item.file_name.lower()
        ]
        if not candidates:
            raise AppException(
                f"Dataset for role '{role}' is not available",
                status_code=404,
                details={"role": role, "marker": marker},
            )

        # Prefer exact stem matches and smaller duplicates last.
        candidates.sort(
            key=lambda item: (
                0 if marker in item.dataset_name.lower() else 1,
                " (" in item.file_name,
                item.file_name,
            )
        )
        return candidates[0]

    def should_stream(self, role: str, dataset: DatasetInfo) -> bool:
        """Choose streaming vs full-load based on role and size policy."""
        if role in self._settings.parsed_always_stream_roles():
            return True
        if role in self._settings.parsed_always_full_roles():
            return False
        return dataset.size_bytes >= self._settings.full_load_max_bytes

    def get_json(self, role: str) -> Any:
        """Lazy-load and cache a JSON dataset (never used for executions)."""
        with self._lock:
            if role in self._json_cache:
                return self._json_cache[role]

        dataset = self.resolve_dataset(role)
        if self.should_stream(role, dataset):
            raise AppException(
                f"Dataset role '{role}' must be streamed, not fully loaded",
                status_code=400,
                details={
                    "role": role,
                    "file_name": dataset.file_name,
                    "size_bytes": dataset.size_bytes,
                },
            )

        path = Path(dataset.absolute_path)
        get_logger().info(
            "Loading JSON dataset role=%s path=%s size_bytes=%d",
            role,
            path,
            dataset.size_bytes,
        )
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        with self._lock:
            self._json_cache[role] = payload
        get_logger().info("Cached JSON dataset role=%s", role)
        return payload

    def get_csv(self, role: str) -> list[dict[str, str]]:
        """Lazy-load and cache a CSV dataset as row dictionaries."""
        with self._lock:
            if role in self._csv_cache:
                return self._csv_cache[role]

        dataset = self.resolve_dataset(role)
        path = Path(dataset.absolute_path)
        get_logger().info(
            "Loading CSV dataset role=%s path=%s size_bytes=%d",
            role,
            path,
            dataset.size_bytes,
        )
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = [dict(row) for row in reader]

        with self._lock:
            self._csv_cache[role] = rows
        get_logger().info("Cached CSV dataset role=%s rows=%d", role, len(rows))
        return rows

    def get_clustering(self) -> Any:
        return self.get_json("clustering")

    def get_embeddings(self) -> Any:
        return self.get_json("embeddings")

    def get_failure_summary(self) -> Any:
        return self.get_json("failure_summary")

    def get_metadata(self) -> Any:
        return self.get_json("metadata")

    def get_cpm_report(self) -> Any:
        return self.get_json("cpm")

    def iter_executions(self) -> Iterator[dict[str, Any]]:
        """
        Stream execution records one-by-one.

        Never loads the full executions file into memory.
        """
        dataset = self.resolve_dataset("executions")
        if not self.should_stream("executions", dataset):
            # Safety: executions are always streamed regardless of misconfig.
            get_logger().warning(
                "Executions role forced to streaming despite config path=%s",
                dataset.absolute_path,
            )

        path = Path(dataset.absolute_path)
        logger = get_logger()
        logger.info(
            "Execution stream started path=%s size_bytes=%d",
            path,
            dataset.size_bytes,
        )

        count = 0
        with path.open("rb") as handle:
            for item in ijson.items(handle, "executions.item"):
                if not isinstance(item, dict):
                    continue
                count += 1
                yield item

        with self._lock:
            self._stream_markers.add("executions")
        logger.info("Execution stream completed records=%d", count)

    def has_cached(self, role: str) -> bool:
        with self._lock:
            return role in self._json_cache or role in self._csv_cache

    def was_executions_streamed(self) -> bool:
        with self._lock:
            return "executions" in self._stream_markers


_data_loader: DataLoader | None = None
_loader_lock = RLock()


def get_data_loader(
    settings: Settings | None = None,
    dataset_service: DatasetService | None = None,
) -> DataLoader:
    """Return the process-wide DataLoader singleton."""
    global _data_loader
    with _loader_lock:
        if _data_loader is None:
            cfg = settings or get_settings()
            service = dataset_service or get_dataset_service(cfg)
            _data_loader = DataLoader(cfg, service)
        return _data_loader


def reset_data_loader() -> None:
    """Clear the DataLoader singleton."""
    global _data_loader
    with _loader_lock:
        _data_loader = None
