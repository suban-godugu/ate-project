"""WaferVision predict endpoints — analysis stub wired into VERILUMEN API.

Persists every upload and result under the shared personal I/O roots:

  INPUTS  →  C:\\personal\\input all file\\wafer_<session>\\
  OUTPUTS →  C:\\personal\\agent and parser output\\wafer_<session>\\wafer\\
"""

from __future__ import annotations

import base64
import hashlib
import random
from typing import Any

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.models.users import User
from app.services import artifact_store
from app.services.deps import get_optional_user

router = APIRouter(tags=["wafer-predict"])

DEFECTS = [
    ("Center", "LOT_1"),
    ("Donut", "LOT_2"),
    ("Edge-Loc", "LOT_3"),
    ("Edge-Ring", "LOT_4"),
    ("Local", "LOT_5"),
    ("Near-Full", "LOT_6"),
    ("Normal", "LOT_7"),
    ("Random", "LOT_8"),
    ("Scratch", "LOT_9"),
]


def _seed(name: str) -> int:
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def _tiny_png_b64(seed: int) -> str:
    png = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf"
        b"\xc0\x00\x00\x00\x03\x00\x01\x00\x05\xfe\xd4\xef\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    return base64.b64encode(png + seed.to_bytes(4, "big")).decode("ascii")


def _analyze(filename: str, grid_mode: str, grid_size: int | None, image_b64: str | None) -> dict[str, Any]:
    rng = random.Random(_seed(filename))
    defect, lot = DEFECTS[rng.randrange(len(DEFECTS))]
    rows = cols = int(grid_size or 52) if grid_mode == "manual" else 52
    sample_n = min(rows * cols, 96)
    fail_ratio = rng.uniform(0.02, 0.35)
    fail = int(sample_n * fail_ratio)
    good = sample_n - fail
    yield_pct = round(100.0 * good / sample_n, 2)
    conf = round(rng.uniform(62, 98), 1)

    dies = []
    for i in range(sample_n):
        r, c = divmod(i, cols if cols else 1)
        dies.append(
            {
                "die_id": f"D-{r:02d}-{c:02d}",
                "row": r,
                "column": c,
                "x": c * 10,
                "y": r * 10,
                "status": "FAIL" if i < fail else "PASS",
            }
        )

    clusters = []
    for i in range(rng.randint(2, 6)):
        x0, y0 = rng.randint(5, 80), rng.randint(5, 80)
        w, h = rng.randint(8, 25), rng.randint(8, 25)
        severity = rng.choice(["Critical", "High", "Medium", "Low"])
        clusters.append(
            {
                "rank": i + 1,
                "cluster_id": f"CL-{i+1:03d}",
                "fail": rng.randint(3, 40),
                "good": rng.randint(5, 50),
                "total": rng.randint(10, 90),
                "fail_percent": round(rng.uniform(10, 80), 1),
                "contrib_percent": round(rng.uniform(5, 40), 1),
                "density": round(rng.uniform(0.1, 2.5), 2),
                "severity_score": round(rng.uniform(0.2, 0.99), 2),
                "severity": severity,
                "bbox": [x0, y0, x0 + w, y0 + h],
                "centroid": [x0 + w / 2, y0 + h / 2],
            }
        )

    zones = []
    for i, name in enumerate(["Center", "Mid-Ring", "Edge", "Flat", "Notch"]):
        g, f = rng.randint(20, 200), rng.randint(2, 60)
        t = g + f
        zones.append(
            {
                "zone": name,
                "good": g,
                "fail": f,
                "total": t,
                "yield_percent": round(100 * g / t, 2),
                "fail_percent": round(100 * f / t, 2),
                "density": round(rng.uniform(0.1, 1.8), 2),
                "rank": i + 1,
                "status": rng.choice(["Critical", "Warning", "Healthy"]),
                "polygon": [
                    [10 + i * 5, 10 + i * 3],
                    [40 + i * 5, 12 + i * 2],
                    [45 + i * 4, 40 + i * 3],
                    [12 + i * 3, 42 + i * 2],
                ],
            }
        )

    seed = _seed(filename)
    original = image_b64 or _tiny_png_b64(seed)
    return {
        "wafer_id": f"WAF-{seed % 100000:05d}",
        "assigned_lot": lot,
        "classification": {
            "defect_type": defect,
            "confidence": conf,
            "assigned_lot": lot,
        },
        "yield_summary": {
            "yield_percent": yield_pct,
            "good_dies": good,
            "fail_dies": fail,
            "total_dies": sample_n,
        },
        "grid_info": {"mode": grid_mode, "rows": rows, "columns": cols, "size": rows},
        "dies": dies,
        "images": {
            "original": original,
            "overlay": _tiny_png_b64(seed + 1),
            "density": _tiny_png_b64(seed + 2),
            "gradcam": _tiny_png_b64(seed + 3),
        },
        "spatial_analysis": {
            "cluster_summary": {
                "total_clusters": len(clusters),
                "displayed_clusters": len(clusters),
                "critical_clusters": sum(1 for c in clusters if c["severity"] == "Critical"),
                "largest_cluster": max((c["total"] for c in clusters), default=0),
                "highest_severity": max(
                    (c["severity"] for c in clusters),
                    key=lambda s: {"Critical": 3, "High": 2, "Medium": 1, "Low": 0}.get(s, 0),
                    default="Low",
                ),
            },
            "clusters": clusters,
            "zone_analysis": {"zones": zones},
        },
    }


async def _file_to_bytes(upload: UploadFile) -> tuple[str, bytes]:
    raw = await upload.read()
    name = upload.filename or "wafer.bin"
    return name, raw or b""


def _persist_one(
    session_id: str,
    *,
    name: str,
    raw: bytes,
    grid_mode: str,
    grid_size: int | None,
) -> dict[str, Any]:
    input_path = artifact_store.save_wafer_input_bytes(session_id, name, raw)
    b64 = base64.b64encode(raw).decode("ascii") if raw else _tiny_png_b64(_seed(name))
    result = _analyze(name, grid_mode, grid_size, b64)
    result["source_file"] = name
    result["input_path"] = str(input_path)
    result["session_id"] = session_id

    stem = input_path.stem
    images = result.get("images") or {}
    for kind in ("original", "overlay", "density", "gradcam"):
        artifact_store.save_wafer_image_b64(
            session_id, wafer_stem=stem, kind=kind, b64=images.get(kind)
        )

    out_path = artifact_store.save_wafer_result(
        session_id, result=result, filename=f"{stem}.json"
    )
    result["output_path"] = str(out_path)
    return result


@router.post("/predict")
async def predict(
    image: UploadFile = File(...),
    grid_mode: str = Form("automatic"),
    grid_size: str | None = Form(None),
    _user: User | None = Depends(get_optional_user),
):
    session_id = artifact_store.new_wafer_session_id()
    artifact_store.ensure_job_tree(session_id)
    name, raw = await _file_to_bytes(image)
    size = int(grid_size) if grid_size else None
    return _persist_one(session_id, name=name, raw=raw, grid_mode=grid_mode, grid_size=size)


@router.post("/predict/batch")
async def predict_batch(
    images: list[UploadFile] = File(...),
    grid_mode: str = Form("automatic"),
    grid_size: str | None = Form(None),
    _user: User | None = Depends(get_optional_user),
):
    session_id = artifact_store.new_wafer_session_id()
    artifact_store.ensure_job_tree(session_id)
    size = int(grid_size) if grid_size else None
    out: list[dict[str, Any]] = []
    for upload in images:
        name, raw = await _file_to_bytes(upload)
        out.append(
            _persist_one(session_id, name=name, raw=raw, grid_mode=grid_mode, grid_size=size)
        )
    batch_path = artifact_store.save_wafer_result(
        session_id, result=out, filename="batch_result.json"
    )
    artifact_store.append_log(
        session_id, f"wafer batch complete count={len(out)} path={batch_path}"
    )
    return out
