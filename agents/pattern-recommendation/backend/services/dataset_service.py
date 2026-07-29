"""Dataset discovery service and in-memory registry."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from backend.core.config import Settings
from backend.core.logging import get_logger
from backend.schemas.datasets import (
    DatasetInfo,
    DatasetList,
    DatasetStatus,
    DatasetSummary,
)
from backend.utils.dataset_fs import (
    classify_dataset_type,
    collect_file_metadata,
    unique_dataset_name,
    validate_dataset_file,
)


class DatasetRegistry:
    """Thread-safe in-memory registry of discovered datasets."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._datasets: dict[str, DatasetInfo] = {}
        self._discovery_timestamp: datetime | None = None

    def replace_all(
        self,
        datasets: list[DatasetInfo],
        *,
        timestamp: datetime | None = None,
    ) -> None:
        with self._lock:
            self._datasets = {item.dataset_name: item for item in datasets}
            self._discovery_timestamp = timestamp or datetime.now(timezone.utc)

    def list_datasets(self) -> list[DatasetInfo]:
        with self._lock:
            return sorted(
                self._datasets.values(),
                key=lambda item: (item.dataset_type, item.file_name, item.dataset_name),
            )

    @property
    def discovery_timestamp(self) -> datetime | None:
        with self._lock:
            return self._discovery_timestamp

    def status_counts(self) -> DatasetStatus:
        with self._lock:
            available = missing = invalid = 0
            for item in self._datasets.values():
                if item.status == "available":
                    available += 1
                elif item.status == "missing":
                    missing += 1
                else:
                    invalid += 1
            total = available + missing + invalid
            return DatasetStatus(
                available=available,
                missing=missing,
                invalid=invalid,
                total=total,
            )


class DatasetService:
    """Discover and cache analysis datasets from configured directories."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._registry = DatasetRegistry()
        self._lock = RLock()

    @property
    def registry(self) -> DatasetRegistry:
        return self._registry

    def discover(self) -> DatasetList:
        """Scan configured directories and replace the in-memory registry."""
        logger = get_logger()
        logger.info(
            "Dataset discovery started data_dir=%s output_dir=%s",
            self._settings.data_dir,
            self._settings.output_dir,
        )

        discovered: list[DatasetInfo] = []
        seen_names: set[str] = set()
        matched_paths: set[Path] = set()

        for pattern in self._settings.parsed_data_patterns():
            discovered.extend(
                self._scan_pattern(
                    root=self._settings.data_dir,
                    root_label="data",
                    pattern=pattern,
                    seen_names=seen_names,
                    matched_paths=matched_paths,
                )
            )

        for pattern in self._settings.parsed_output_patterns():
            discovered.extend(
                self._scan_pattern(
                    root=self._settings.output_dir,
                    root_label="output",
                    pattern=pattern,
                    seen_names=seen_names,
                    matched_paths=matched_paths,
                )
            )

        timestamp = datetime.now(timezone.utc)
        with self._lock:
            self._registry.replace_all(discovered, timestamp=timestamp)

        status = self._registry.status_counts()
        logger.info(
            "Dataset discovery completed total=%d available=%d missing=%d invalid=%d",
            status.total,
            status.available,
            status.missing,
            status.invalid,
        )
        return self.get_datasets()

    def refresh(self) -> DatasetList:
        """Rescan directories and update the registry."""
        logger = get_logger()
        logger.info("Dataset discovery refresh requested")
        result = self.discover()
        logger.info(
            "Dataset discovery refresh completed total=%d",
            result.total,
        )
        return result

    def get_datasets(self) -> DatasetList:
        datasets = self._registry.list_datasets()
        return DatasetList(
            datasets=datasets,
            total=len(datasets),
            discovery_timestamp=self._registry.discovery_timestamp,
        )

    def get_status(self) -> DatasetStatus:
        return self._registry.status_counts()

    def get_summary(self) -> DatasetSummary:
        datasets = self._registry.list_datasets()
        status = self._registry.status_counts()
        file_types: dict[str, int] = {}
        total_storage = 0
        for item in datasets:
            if item.status != "available":
                continue
            extension = item.extension or "unknown"
            file_types[extension] = file_types.get(extension, 0) + 1
            total_storage += item.size_bytes
        return DatasetSummary(
            dataset_counts=status,
            file_types=file_types,
            total_storage_bytes=total_storage,
            discovery_timestamp=self._registry.discovery_timestamp,
            data_dir=str(self._settings.data_dir.resolve()),
            output_dir=str(self._settings.output_dir.resolve()),
        )

    def _scan_pattern(
        self,
        *,
        root: Path,
        root_label: str,
        pattern: str,
        seen_names: set[str],
        matched_paths: set[Path],
    ) -> list[DatasetInfo]:
        logger = get_logger()
        results: list[DatasetInfo] = []

        if not root.exists() or not root.is_dir():
            logger.warning(
                "Dataset root missing or not a directory root=%s path=%s pattern=%s",
                root_label,
                root,
                pattern,
            )
            results.append(
                DatasetInfo(
                    dataset_name=unique_dataset_name(
                        f"missing_{root_label}_{_safe_token(pattern)}",
                        seen_names,
                    ),
                    dataset_type="unknown",
                    file_name=pattern,
                    absolute_path=str((root / pattern).resolve()),
                    extension=_extension_from_pattern(pattern),
                    size_bytes=0,
                    last_modified="",
                    status="missing",
                    pattern=pattern,
                    root=root_label,
                )
            )
            seen_names.add(results[-1].dataset_name)
            return results

        matches = sorted(
            path for path in root.rglob(pattern) if path.is_file()
        )
        # Deduplicate identical resolved paths across overlapping patterns.
        unique_matches: list[Path] = []
        for path in matches:
            resolved = path.resolve()
            if resolved in matched_paths:
                continue
            matched_paths.add(resolved)
            unique_matches.append(path)

        # Only mark missing when the pattern matches nothing on disk.
        # Overlapping patterns that already claimed the same files are fine.
        if not matches:
            logger.warning(
                "Dataset missing root=%s pattern=%s",
                root_label,
                pattern,
            )
            name = unique_dataset_name(
                f"missing_{_safe_token(pattern)}",
                seen_names,
            )
            seen_names.add(name)
            results.append(
                DatasetInfo(
                    dataset_name=name,
                    dataset_type=classify_dataset_type(
                        pattern, self._settings.parsed_type_rules()
                    ),
                    file_name=pattern,
                    absolute_path=str((root / pattern).resolve()),
                    extension=_extension_from_pattern(pattern),
                    size_bytes=0,
                    last_modified="",
                    status="missing",
                    pattern=pattern,
                    root=root_label,
                )
            )
            return results

        if not unique_matches:
            return results

        type_rules = self._settings.parsed_type_rules()
        for path in unique_matches:
            status, reason = validate_dataset_file(path)
            dataset_name = unique_dataset_name(path.stem, seen_names)
            seen_names.add(dataset_name)
            metadata = (
                collect_file_metadata(path)
                if status == "available"
                else {
                    "size_bytes": 0,
                    "last_modified": "",
                    "extension": path.suffix.lower().lstrip("."),
                }
            )
            info = DatasetInfo(
                dataset_name=dataset_name,
                dataset_type=classify_dataset_type(path.name, type_rules),
                file_name=path.name,
                absolute_path=str(path.resolve()),
                extension=str(metadata["extension"]),
                size_bytes=int(metadata["size_bytes"]),
                last_modified=str(metadata["last_modified"]),
                status=status,
                pattern=pattern,
                root=root_label,
            )
            results.append(info)
            if status == "available":
                logger.info(
                    "Dataset found name=%s type=%s path=%s size_bytes=%d",
                    info.dataset_name,
                    info.dataset_type,
                    info.absolute_path,
                    info.size_bytes,
                )
            elif status == "missing":
                logger.warning(
                    "Dataset missing name=%s path=%s",
                    info.dataset_name,
                    info.absolute_path,
                )
            else:
                logger.warning(
                    "Dataset invalid name=%s path=%s reason=%s",
                    info.dataset_name,
                    info.absolute_path,
                    reason,
                )
        return results


def _safe_token(value: str) -> str:
    return (
        value.replace("*", "star")
        .replace("?", "q")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(".", "_")
        .replace("-", "_")
    )


def _extension_from_pattern(pattern: str) -> str:
    suffix = Path(pattern).suffix.lower().lstrip(".")
    if not suffix or "*" in suffix or "?" in suffix:
        return ""
    return suffix


_dataset_service: DatasetService | None = None
_service_lock = RLock()


def get_dataset_service(settings: Settings | None = None) -> DatasetService:
    """Return the process-wide DatasetService singleton."""
    global _dataset_service
    with _service_lock:
        if _dataset_service is None:
            from backend.core.config import get_settings

            _dataset_service = DatasetService(settings or get_settings())
        return _dataset_service


def reset_dataset_service() -> None:
    """Clear the singleton (tests / app reconfiguration)."""
    global _dataset_service
    with _service_lock:
        _dataset_service = None
