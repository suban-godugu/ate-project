"""Local audit/output tree for parser + agent artifacts.

Strict layout (do not write job files elsewhere):

  INPUTS  →  C:\\personal\\input all file\\<job_id>\\
             (STIL, ATE logs, original ZIP only)

  OUTPUTS →  C:\\personal\\agent and parser output\\<job_id>\\
             parser|pattern|failure|scan|recommendation|dashboard|reports|logs|cost|wafer
"""

from __future__ import annotations

import base64
import json
import logging
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.config import get_settings

log = logging.getLogger("verilumen.artifact_store")

SUBDIRS = (
    "parser",
    "pattern",
    "failure",
    "scan",
    "recommendation",
    "dashboard",
    "reports",
    "logs",
    "cost",
    "wafer",
)

STIL_EXTS = {".stil"}
LOG_EXTS = {".log", ".txt"}
INPUT_EXTS = STIL_EXTS | LOG_EXTS
WAFER_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}


def job_root(job_id: str) -> Path:
    return Path(get_settings().agent_output_root) / str(job_id)


def ensure_job_tree(job_id: str) -> Path:
    root = job_root(job_id)
    for name in SUBDIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def write_json(job_id: str, category: str, filename: str, payload: Any) -> Path:
    ensure_job_tree(job_id)
    path = job_root(job_id) / category / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def write_text(job_id: str, category: str, filename: str, text: str) -> Path:
    ensure_job_tree(job_id)
    path = job_root(job_id) / category / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def write_bytes(job_id: str, category: str, filename: str, data: bytes) -> Path:
    ensure_job_tree(job_id)
    path = job_root(job_id) / category / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def append_log(job_id: str, message: str, *, level: str = "INFO") -> Path:
    ensure_job_tree(job_id)
    path = job_root(job_id) / "logs" / "pipeline.log"
    line = f"{datetime.now(UTC).isoformat()} [{level}] {message}\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)
    return path


def dataset_path(job_id: str) -> Path:
    return job_root(job_id) / "parser" / "unified_dataset.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def upload_input_job_dir(job_id: str) -> Path:
    """C:\\personal\\input all file\\<job_id>\\ — sole durable input location."""
    root = Path(get_settings().upload_input_root) / str(job_id)
    root.mkdir(parents=True, exist_ok=True)
    return root


def list_job_input_files(job_id: str) -> list[Path]:
    """STIL/LOG files under input all file/<job_id>/ (never from the output tree)."""
    folder = upload_input_job_dir(job_id)
    if not folder.exists():
        return []
    out: list[Path] = []
    for p in sorted(folder.iterdir(), key=lambda x: x.name.lower()):
        if not p.is_file():
            continue
        if p.name.startswith("_original_"):
            continue
        if p.suffix.lower() in INPUT_EXTS:
            out.append(p)
    return out


def place_input_ref(src: Path, dest: Path) -> str:
    """Expose an input file at dest without storing a second copy of the bytes.

    Preference: hardlink → symlink. Raises if neither works.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        try:
            dest.unlink()
        except OSError:
            pass
    try:
        os.link(src, dest)
        return "hardlink"
    except OSError:
        pass
    os.symlink(src, dest)
    return "symlink"


def save_upload_files_to_input_root(
    job_id: str,
    *,
    original_name: str,
    original_bytes: bytes | None = None,
    original_path: Path | None = None,
    work_files: list[Path] | None = None,
) -> Path:
    """Store original upload + extracted STIL/logs into UPLOAD_INPUT_ROOT/<job_id>/."""
    dest_root = upload_input_job_dir(job_id)
    saved: list[str] = []

    try:
        orig_name = Path(original_name).name or "upload.bin"
        orig_dest = dest_root / f"_original_{orig_name}"
        if original_path is not None and original_path.exists():
            shutil.copy2(original_path, orig_dest)
        elif original_bytes is not None:
            orig_dest.write_bytes(original_bytes)
        if orig_dest.exists():
            saved.append(orig_dest.name)
    except Exception as exc:  # noqa: BLE001
        log.warning("save_original_upload_failed", extra={"structured_extra": {"error": str(exc)}})

    for path in work_files or []:
        try:
            if not path.exists():
                continue
            target = dest_root / path.name
            if target.resolve() == (dest_root / f"_original_{path.name}").resolve():
                continue
            shutil.copy2(path, target)
            saved.append(path.name)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "save_work_file_failed",
                extra={"structured_extra": {"file": path.name, "error": str(exc)}},
            )

    try:
        write_json(
            job_id,
            "parser",
            "upload_input_mirror.json",
            {"input_root": str(dest_root), "saved_files": saved},
        )
        append_log(job_id, f"upload files mirrored to {dest_root} count={len(saved)}")
    except Exception:  # noqa: BLE001
        pass

    return dest_root


def new_wafer_session_id() -> str:
    """Unique wafer batch/session folder name under the personal I/O roots."""
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S_%f")
    return f"wafer_{stamp}"


def save_wafer_input_bytes(session_id: str, filename: str, data: bytes) -> Path:
    """Store a wafer map under ``input all file/<session_id>/``."""
    safe = Path(filename).name or "wafer.bin"
    dest = upload_input_job_dir(session_id) / safe
    # Avoid overwrite collisions within the same session
    if dest.exists():
        stem, suffix = dest.stem, dest.suffix
        n = 1
        while True:
            candidate = dest.with_name(f"{stem}_{n}{suffix}")
            if not candidate.exists():
                dest = candidate
                break
            n += 1
    dest.write_bytes(data)
    append_log(session_id, f"wafer input saved: {dest.name} ({len(data)} bytes)")
    return dest


def save_wafer_result(
    session_id: str,
    *,
    result: dict[str, Any] | list[Any],
    filename: str = "result.json",
) -> Path:
    """Store wafer analysis JSON under ``agent and parser output/<session_id>/wafer/``."""
    # Drop base64 image blobs from durable metadata (images saved separately).
    def _strip_images(payload: Any) -> Any:
        if isinstance(payload, list):
            return [_strip_images(item) for item in payload]
        if isinstance(payload, dict):
            out = {k: v for k, v in payload.items() if k != "images"}
            return {k: _strip_images(v) for k, v in out.items()}
        return payload

    path = write_json(session_id, "wafer", filename, _strip_images(result))
    append_log(session_id, f"wafer result saved: wafer/{filename}")
    return path


def save_cost_intelligence_artifacts(
    job_id: str,
    *,
    summary: dict[str, Any] | None = None,
    scan_chain: dict[str, Any] | None = None,
    wafer: dict[str, Any] | None = None,
    overview: dict[str, Any] | None = None,
    input_manifest: dict[str, Any] | None = None,
) -> Path:
    """Persist Cost Intelligence I/O under the personal roots.

    Inputs already live in ``input all file/<job_id>/``.
    Outputs go to ``agent and parser output/<job_id>/cost/``.
    """
    ensure_job_tree(job_id)
    root = job_root(job_id) / "cost"
    root.mkdir(parents=True, exist_ok=True)

    paths: list[str] = []
    if summary is not None:
        paths.append(str(write_json(job_id, "cost", "log_cost_summary.json", summary)))
    if overview is not None:
        paths.append(str(write_json(job_id, "cost", "overview.json", overview)))
    if scan_chain is not None:
        paths.append(str(write_json(job_id, "cost", "scan_chain_cost.json", scan_chain)))
    if wafer is not None:
        paths.append(str(write_json(job_id, "cost", "wafer_cost.json", wafer)))
    if input_manifest is not None:
        paths.append(str(write_json(job_id, "cost", "input_manifest.json", input_manifest)))

    index = {
        "job_id": job_id,
        "input_root": str(upload_input_job_dir(job_id)),
        "output_root": str(root),
        "written": paths,
        "written_at": datetime.now(UTC).isoformat(),
    }
    index_path = write_json(job_id, "cost", "index.json", index)
    append_log(job_id, f"cost intelligence artifacts saved count={len(paths)} root={root}")
    return index_path


def save_wafer_image_b64(
    session_id: str,
    *,
    wafer_stem: str,
    kind: str,
    b64: str | None,
) -> Path | None:
    """Decode a base64 PNG/JPEG (or raw) into ``wafer/images/``."""
    if not b64:
        return None
    try:
        raw = b64.split(",", 1)[-1] if b64.startswith("data:") else b64
        data = base64.b64decode(raw)
    except Exception as exc:  # noqa: BLE001
        log.warning("wafer_image_decode_failed", extra={"structured_extra": {"error": str(exc)}})
        return None
    safe_stem = Path(wafer_stem).stem or "wafer"
    safe_kind = "".join(c if c.isalnum() or c in "-_" else "_" for c in kind) or "image"
    return write_bytes(session_id, "wafer", f"images/{safe_stem}_{safe_kind}.png", data)
