"""Bridge job inputs → Scan Diagnosis live dirs without duplicating input bytes.

Canonical inputs live only under:
  C:\\personal\\input all file\\<job_id>\\

Scan's live engine still expects files under data/stil + data/logs, so this
module places hardlinks/symlinks there (same bytes, no second copy).
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

from app.core.config import get_settings
from app.services import artifact_store

log = logging.getLogger("verilumen.scan_diagnosis_bridge")

STIL_EXTS = {".stil"}
LOG_EXTS = {".log", ".txt"}


def scan_data_root() -> Path:
    settings = get_settings()
    configured = getattr(settings, "scan_diagnosis_data_dir", None)
    if configured:
        return Path(configured)
    return Path(r"C:\personal\Scan-diagnosis-Agent-v1.1-main\data")


def _clear_agent_cache(data_root: Path) -> None:
    cache = data_root / "cache"
    if not cache.exists():
        return
    for p in cache.glob("*"):
        try:
            if p.is_file() or p.is_symlink():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
        except OSError as exc:
            log.warning("cache_clear_failed", extra={"structured_extra": {"path": str(p), "error": str(exc)}})


def collect_job_input_files(job_id: str) -> list[Path]:
    """Inputs only from C:\\personal\\input all file\\<job_id>\\."""
    return artifact_store.list_job_input_files(job_id)


def publish_job_to_scan_diagnosis(job_id: str, *, work_files: list[Path] | None = None) -> dict:
    """
    Point Scan live UI at job inputs without copying file bytes.

    Layout (hardlink/symlink views):
      <scan_data>/stil/<name>.stil
      <scan_data>/logs/platform_<job_id>/<name>.log
    Source of truth remains input all file/<job_id>/.
    """
    data_root = scan_data_root()
    stil_dir = data_root / "stil"
    logs_root = data_root / "logs"
    lot_dir = logs_root / f"platform_{job_id[:8]}"
    stil_dir.mkdir(parents=True, exist_ok=True)
    lot_dir.mkdir(parents=True, exist_ok=True)

    sources = collect_job_input_files(job_id)
    if not sources and work_files:
        sources = list(work_files)

    stil_linked: list[str] = []
    log_linked: list[str] = []
    methods: list[str] = []

    for src in sources:
        try:
            if not src.exists() or not src.is_file():
                continue
            suf = src.suffix.lower()
            if suf in STIL_EXTS:
                dest = stil_dir / src.name
                methods.append(artifact_store.place_input_ref(src, dest))
                stil_linked.append(dest.name)
            elif suf in LOG_EXTS:
                dest_name = src.name if suf == ".log" else f"{src.stem}.log"
                dest = lot_dir / dest_name
                methods.append(artifact_store.place_input_ref(src, dest))
                log_linked.append(f"{lot_dir.name}/{dest.name}")
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "scan_publish_file_failed",
                extra={"structured_extra": {"file": str(src), "error": str(exc)}},
            )

    _clear_agent_cache(data_root)

    result = {
        "data_root": str(data_root),
        "stil_dir": str(stil_dir),
        "logs_dir": str(lot_dir),
        "input_root": str(artifact_store.upload_input_job_dir(job_id)),
        "stil_files": stil_linked,
        "log_files": log_linked,
        "stil_count": len(stil_linked),
        "log_count": len(log_linked),
        "link_methods": sorted(set(methods)),
        "copied_bytes": False,
    }
    try:
        artifact_store.write_json(job_id, "scan", "live_inputs_publish.json", result)
        artifact_store.append_log(
            job_id,
            f"published to Scan Diagnosis (link) stil={len(stil_linked)} logs={len(log_linked)} "
            f"methods={result['link_methods']} input_root={result['input_root']}",
        )
    except Exception:  # noqa: BLE001
        pass

    log.info(
        "scan_diagnosis_inputs_published",
        extra={"structured_extra": {"job_id": job_id, **result}},
    )
    return result
