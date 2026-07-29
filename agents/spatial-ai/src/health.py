"""
Operational health and metrics helpers for WaferVision-AI.

Read-only process / environment checks. Does not alter inference behaviour.
"""

from __future__ import annotations

import os
import platform
import shutil
import time
from pathlib import Path
from typing import Any

from .config import (
    APP_ENV,
    APP_NAME,
    APP_VERSION,
    LOGS_DIR,
    MODEL_PATH,
    MODEL_VERSION,
    PROJECT_ROOT,
    TEMP_DIR,
)

_PROCESS_STARTED_AT = time.time()


def _model_loaded() -> bool:
    try:
        from .predict import get_prediction_model

        get_prediction_model()
        return True
    except Exception:  # noqa: BLE001
        return False


def _optional_psutil_metrics() -> dict[str, Any]:
    try:
        import psutil  # type: ignore

        process = psutil.Process(os.getpid())
        mem = process.memory_info()
        disk = shutil.disk_usage(str(PROJECT_ROOT))
        return {
            "memory": {
                "rss_bytes": int(mem.rss),
                "vms_bytes": int(mem.vms),
                "percent": float(process.memory_percent()),
            },
            "cpu": {
                "process_percent": float(process.cpu_percent(interval=0.0)),
                "system_percent": float(psutil.cpu_percent(interval=0.0)),
                "count": int(psutil.cpu_count() or 0),
            },
            "disk": {
                "total_bytes": int(disk.total),
                "used_bytes": int(disk.used),
                "free_bytes": int(disk.free),
                "percent_used": round(100.0 * disk.used / disk.total, 2)
                if disk.total
                else 0.0,
            },
        }
    except Exception:  # noqa: BLE001
        disk = shutil.disk_usage(str(PROJECT_ROOT))
        return {
            "memory": {"rss_bytes": None, "note": "Install psutil for detailed metrics"},
            "cpu": {"note": "Install psutil for detailed metrics"},
            "disk": {
                "total_bytes": int(disk.total),
                "used_bytes": int(disk.used),
                "free_bytes": int(disk.free),
            },
        }


def get_version_info() -> dict[str, Any]:
    """
    Return semantic version metadata.

    Returns:
        Dict with application and model version fields.
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "model_version": MODEL_VERSION,
        "environment": APP_ENV,
        "api": "v1",
    }


def get_health_status() -> dict[str, Any]:
    """
    Return readiness / liveness style health payload.

    Returns:
        Dict describing API status and model load state.
    """
    model_exists = Path(MODEL_PATH).is_file()
    loaded = _model_loaded() if model_exists else False
    status = "ok" if loaded else ("degraded" if model_exists else "error")
    return {
        "status": status,
        "api_running": True,
        "model_path": str(MODEL_PATH),
        "model_file_present": model_exists,
        "model_loaded": loaded,
        "environment": APP_ENV,
        "uptime_seconds": round(time.time() - _PROCESS_STARTED_AT, 2),
        "logs_dir": str(LOGS_DIR),
        "temp_dir": str(TEMP_DIR),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }


def get_metrics() -> dict[str, Any]:
    """
    Return lightweight operational metrics.

    Returns:
        Dict with process resource statistics when available.
    """
    payload = {
        "version": APP_VERSION,
        "uptime_seconds": round(time.time() - _PROCESS_STARTED_AT, 2),
        "model_loaded": _model_loaded(),
        "pid": os.getpid(),
    }
    payload.update(_optional_psutil_metrics())
    return payload


__all__ = [
    "get_version_info",
    "get_health_status",
    "get_metrics",
]
