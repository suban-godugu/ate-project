"""
Required Test Optimization Recommendation Agent inputs.

Inputs live under:
  C:\\personal\\input all file\\test-optimization
  → one or more OptimizationContext JSON files (*_context.json or any .json)

Outputs live under:
  C:\\personal\\agent and parser output\\test-optimization
  → recommendations/*.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..core.config import Settings, get_settings
from ..core.logging import get_logger
from ..domain.models import OptimizationContext
from ..services.optimization_service import OptimizationService

logger = get_logger(__name__)


def _file_meta(path: Path) -> dict[str, Any]:
    exists = path.is_file()
    return {
        "path": str(path),
        "name": path.name,
        "exists": exists,
        "size_bytes": path.stat().st_size if exists else 0,
        "mtime": path.stat().st_mtime if exists else None,
    }


def _looks_like_context(payload: dict[str, Any]) -> bool:
    if "context" in payload and isinstance(payload["context"], dict):
        return True
    # Bare OptimizationContext — device/lot_id are enough to attempt validation.
    return "device" in payload or "lot_id" in payload or "yield_data" in payload


def discover_context_files(input_dir: Path) -> list[Path]:
    if not input_dir.is_dir():
        return []
    files = sorted(
        [
            p
            for p in input_dir.iterdir()
            if p.is_file() and p.suffix.lower() == ".json" and not p.name.startswith("_")
        ],
        key=lambda p: p.name.lower(),
    )
    return files


def input_inventory(settings: Settings | None = None) -> dict[str, Any]:
    cfg = settings or get_settings()
    input_dir = Path(cfg.input_dir)
    output_dir = Path(cfg.data_dir)
    files = discover_context_files(input_dir)

    inputs: list[dict[str, Any]] = []
    valid = 0
    invalid = 0
    for path in files:
        meta = _file_meta(path)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not _looks_like_context(payload):
                meta["valid"] = False
                meta["error"] = "Not an OptimizationContext JSON object"
                invalid += 1
            else:
                body = payload.get("context") if "context" in payload else payload
                ctx = OptimizationContext.model_validate(body)
                meta["valid"] = True
                meta["device"] = ctx.device
                meta["lot_id"] = ctx.lot_id
                meta["fab"] = ctx.fab
                valid += 1
        except Exception as exc:  # noqa: BLE001
            meta["valid"] = False
            meta["error"] = str(exc)
            invalid += 1
        inputs.append(
            {
                "id": path.stem,
                "label": path.name,
                "pattern": "*.json (OptimizationContext)",
                "required": True,
                **meta,
            }
        )

    rec_dir = output_dir / "recommendations"
    rec_count = len(list(rec_dir.glob("*.json"))) if rec_dir.is_dir() else 0
    ready = valid > 0

    return {
        "data_dir": str(output_dir),
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "ready": ready,
        "missing": [] if ready else ["optimization_context_json"],
        "valid_contexts": valid,
        "invalid_contexts": invalid,
        "inputs": inputs,
        "recommendations": {
            "id": "recommendations",
            "label": "Persisted recommendations",
            "path": str(rec_dir),
            "count": rec_count,
        },
    }


async def connect_inputs(
    service: OptimizationService,
    settings: Settings | None = None,
    *,
    persist: bool = True,
) -> dict[str, Any]:
    """Validate input contexts and run optimize on each, persisting results."""
    cfg = settings or get_settings()
    inventory = input_inventory(cfg)
    if not inventory["ready"]:
        return {
            "status": "missing_inputs",
            "message": (
                "No OptimizationContext JSON found — place files under "
                f"{inventory['input_dir']}"
            ),
            **inventory,
        }

    results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for item in inventory["inputs"]:
        if not item.get("valid"):
            errors.append(
                {
                    "file": item.get("name"),
                    "error": item.get("error") or "invalid context",
                }
            )
            continue
        path = Path(item["path"])
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            body = payload.get("context") if "context" in payload else payload
            ctx = OptimizationContext.model_validate(body)
            rec = await service.optimize(ctx, persist=persist)
            results.append(
                {
                    "file": path.name,
                    "recommendation_id": rec.id,
                    "device": rec.device,
                    "lot_id": rec.lot_id,
                    "risk_level": rec.risk_level,
                    "confidence": rec.confidence,
                    "recommended_strategy": rec.recommended_strategy,
                    "engine": rec.engine,
                }
            )
            logger.info(
                "Connected context %s -> recommendation %s (%s)",
                path.name,
                rec.id,
                rec.risk_level,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to optimize context %s", path)
            errors.append({"file": path.name, "error": str(exc)})

    refreshed = input_inventory(cfg)
    status = "connected" if results else "failed"
    return {
        "status": status,
        "message": (
            f"Optimized {len(results)} OptimizationContext file(s)"
            if results
            else "No contexts could be optimized"
        ),
        "optimized": results,
        "errors": errors,
        **refreshed,
    }
