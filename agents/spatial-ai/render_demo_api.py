"""Lightweight WaferVision API for Render (no Torch / no .pth required).

Classifies into the 9 WM-811k-style lots from the filename when possible:
Center, Donut, Edge-Loc, Edge-Ring, Local, Near-Full, Normal, Random, Scratch.

Deploy as ``ate-wafer-api``. Dashboard:
  NEXT_PUBLIC_WAFER_API_URL=https://ate-wafer-api.onrender.com
"""

from __future__ import annotations

import base64
import hashlib
import math
import os
import random
import re
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Permanent taxonomy — must match dashboard LOT_TAXONOMY
DEFECT_TO_LOT: dict[str, str] = {
    "Center": "LOT_1",
    "Donut": "LOT_2",
    "Edge-Loc": "LOT_3",
    "Edge-Ring": "LOT_4",
    "Local": "LOT_5",
    "Near-Full": "LOT_6",
    "Normal": "LOT_7",
    "Random": "LOT_8",
    "Scratch": "LOT_9",
}
DEFECT_CLASSES = tuple(DEFECT_TO_LOT.keys())

IMG_SIZE = 224
_DEFAULT_ORIGINS = (
    "https://ate-project-ochre.vercel.app,"
    "http://localhost:3000,"
    "http://127.0.0.1:3000"
)

# Filename tokens → class (order matters: longer / specific first)
_FILENAME_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"near[-_]?full|nearfull", re.I), "Near-Full"),
    (re.compile(r"edge[-_]?ring|edgering", re.I), "Edge-Ring"),
    (re.compile(r"edge[-_]?loc|edgeloc|\bEL[_-]", re.I), "Edge-Loc"),
    (re.compile(r"\bscratch\b|\bS[_-]\d", re.I), "Scratch"),
    (re.compile(r"\brandom\b", re.I), "Random"),
    (re.compile(r"\bnormal\b", re.I), "Normal"),
    (re.compile(r"\blocal\b", re.I), "Local"),
    (re.compile(r"\bdonut\b", re.I), "Donut"),
    (re.compile(r"\bcenter\b", re.I), "Center"),
]


def _origins() -> list[str]:
    raw = os.getenv("WAFERVISION_ALLOWED_ORIGINS", _DEFAULT_ORIGINS)
    return [o.strip() for o in raw.split(",") if o.strip()]


app = FastAPI(title="WaferVision-AI API (Render Demo)", version="1.1.0-demo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _seed(name: str) -> int:
    return int(hashlib.md5(name.encode()).hexdigest()[:8], 16)


def detect_defect_from_filename(filename: str) -> str | None:
    """Map labeled dataset filenames to one of the 9 defect classes."""
    base = filename.replace("\\", "/").split("/")[-1]
    for pattern, defect in _FILENAME_RULES:
        if pattern.search(base):
            return defect
    return None


def _in_wafer(r: int, c: int, rows: int, cols: int) -> bool:
    cy, cx = (rows - 1) / 2.0, (cols - 1) / 2.0
    radius = min(rows, cols) / 2.0 - 0.5
    return (r - cy) ** 2 + (c - cx) ** 2 <= radius**2


def _fail_mask(defect: str, rows: int, cols: int, rng: random.Random) -> list[list[bool]]:
    """Generate a die FAIL mask that roughly matches the defect pattern."""
    cy, cx = (rows - 1) / 2.0, (cols - 1) / 2.0
    radius = min(rows, cols) / 2.0 - 0.5
    mask = [[False] * cols for _ in range(rows)]

    for r in range(rows):
        for c in range(cols):
            if not _in_wafer(r, c, rows, cols):
                continue
            dy, dx = (r - cy) / radius, (c - cx) / radius
            dist = math.sqrt(dx * dx + dy * dy)
            ang = math.atan2(dy, dx)
            fail = False

            if defect == "Center":
                fail = dist < 0.28 or (dist < 0.38 and rng.random() < 0.35)
            elif defect == "Donut":
                fail = 0.22 < dist < 0.48 or (0.18 < dist < 0.55 and rng.random() < 0.25)
            elif defect == "Edge-Loc":
                fail = dist > 0.72 and abs(ang) < 1.1  # right-side arc
                fail = fail or (dist > 0.78 and rng.random() < 0.2)
            elif defect == "Edge-Ring":
                fail = dist > 0.78 or (dist > 0.7 and rng.random() < 0.4)
            elif defect == "Local":
                # a few blobs
                blobs = [(0.35, 0.2), (-0.4, -0.25), (0.1, -0.45)]
                fail = any(
                    (dx - bx) ** 2 + (dy - by) ** 2 < 0.04 for bx, by in blobs
                ) or rng.random() < 0.02
            elif defect == "Near-Full":
                fail = rng.random() < 0.72
            elif defect == "Normal":
                fail = rng.random() < 0.03
            elif defect == "Random":
                fail = rng.random() < 0.22
            elif defect == "Scratch":
                # diagonal band
                fail = abs(dx - dy) < 0.08 or abs(dx - dy + 0.15) < 0.05
                fail = fail or rng.random() < 0.04
            else:
                fail = rng.random() < 0.15

            mask[r][c] = bool(fail)
    return mask


def _build_dies(mask: list[list[bool]], rows: int, cols: int) -> list[dict[str, Any]]:
    pitch = IMG_SIZE / max(rows, cols)
    offset = (IMG_SIZE - cols * pitch) / 2
    dies: list[dict[str, Any]] = []
    for r in range(rows):
        for c in range(cols):
            if not _in_wafer(r, c, rows, cols):
                continue
            x = offset + (c + 0.5) * pitch
            y = offset + (r + 0.5) * pitch
            dies.append(
                {
                    "die_id": f"D-{r:02d}-{c:02d}",
                    "row": r,
                    "column": c,
                    "x": round(x, 2),
                    "y": round(y, 2),
                    "status": "FAIL" if mask[r][c] else "PASS",
                }
            )
    return dies


def _visualization(dies: list[dict[str, Any]], pitch: float) -> dict[str, Any]:
    fail_points = [
        {
            "x": float(d["x"]),
            "y": float(d["y"]),
            "weight": 1.0,
            "die_id": d.get("die_id"),
        }
        for d in dies
        if str(d.get("status", "")).upper() == "FAIL"
    ]
    cx = cy = IMG_SIZE / 2.0
    radius = IMG_SIZE / 2.0 - 2.0
    return {
        "version": 1,
        "coordinate_space": {
            "width": IMG_SIZE,
            "height": IMG_SIZE,
            "units": "model_pixels",
        },
        "rendering": {
            "preferred_canvas_size": 2048,
            "device_pixel_ratio": True,
            "layers": [
                "original",
                "failure_overlay",
                "density",
                "gradcam",
                "clusters",
                "engineering_zones",
                "selection",
            ],
        },
        "original": {
            "type": "die_bins",
            "good_status": "GOOD",
            "fail_status": "FAIL",
            "colors": {
                "background": "#080D17",
                "wafer": "#0D2B33",
                "good": "#14A8A8",
                "fail": "#F2C222",
            },
        },
        "failure_overlay": {
            "status": "FAIL",
            "fill": "#EF4444",
            "alpha": 0.40,
            "alpha_range": [0.30, 0.50],
            "border": "#FF4D4D",
            "border_width_css_px": 1,
            "clip_to_wafer": True,
        },
        "density": {
            "type": "gaussian_kde",
            "points": fail_points,
            "sigma": max(pitch * 1.8, 2.5),
            "radius": max(pitch * 3.0, 9.0),
            "floor": 0.05,
            "normalization": "max",
            "mask": {
                "type": "circle",
                "center_x": cx,
                "center_y": cy,
                "radius": radius,
            },
            "color_stops": [
                {"at": 0.00, "color": "#1D4ED8", "label": "Low"},
                {"at": 0.30, "color": "#16A34A", "label": "Medium"},
                {"at": 0.58, "color": "#FACC15", "label": "High"},
                {"at": 0.80, "color": "#F97316", "label": "Very High"},
                {"at": 1.00, "color": "#DC2626", "label": "Critical"},
            ],
        },
        "gradcam": {
            "available": False,
            "alpha": 0.45,
            "interpolation": "bicubic",
            "heatmap": None,
        },
    }


def _analyze(filename: str, grid_mode: str, grid_size: int | None, image_b64: str | None) -> dict[str, Any]:
    rng = random.Random(_seed(filename))
    defect = detect_defect_from_filename(filename) or rng.choice(list(DEFECT_CLASSES))
    lot = DEFECT_TO_LOT[defect]
    rows = cols = int(grid_size or 52) if grid_mode == "manual" else 52
    rows = cols = max(16, min(rows, 64))

    mask = _fail_mask(defect, rows, cols, rng)
    dies = _build_dies(mask, rows, cols)
    fail = sum(1 for d in dies if d["status"] == "FAIL")
    good = len(dies) - fail
    yield_pct = round(100.0 * good / len(dies), 2) if dies else 0.0
    conf = round(rng.uniform(82, 97), 1) if detect_defect_from_filename(filename) else round(rng.uniform(62, 88), 1)
    pitch = IMG_SIZE / max(rows, cols)

    # Simple cluster + zone stubs for LOT tabs / spatial panels
    fail_dies = [d for d in dies if d["status"] == "FAIL"]
    clusters = []
    if fail_dies:
        for i in range(min(4, max(1, len(fail_dies) // 20))):
            sample = fail_dies[i * 10 : i * 10 + 8] or fail_dies[:5]
            xs = [d["x"] for d in sample]
            ys = [d["y"] for d in sample]
            x0, x1 = min(xs) - 4, max(xs) + 4
            y0, y1 = min(ys) - 4, max(ys) + 4
            clusters.append(
                {
                    "rank": i + 1,
                    "cluster_id": f"CL-{i + 1:03d}",
                    "fail": len(sample),
                    "good": rng.randint(2, 20),
                    "total": len(sample) + rng.randint(2, 20),
                    "fail_percent": round(rng.uniform(20, 80), 1),
                    "contrib_percent": round(100.0 / max(len(fail_dies), 1) * len(sample), 1),
                    "density": round(rng.uniform(0.4, 2.2), 2),
                    "severity_score": round(rng.uniform(0.3, 0.95), 2),
                    "severity": rng.choice(["Critical", "High", "Medium", "Low"]),
                    "bbox": [x0, y0, x1, y1],
                    "centroid": [(x0 + x1) / 2, (y0 + y1) / 2],
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

    return {
        "wafer_id": f"WAF-{_seed(filename) % 100000:05d}",
        "source_file": filename,
        "assigned_lot": lot,
        "lot": lot,
        "classification": {
            "defect_type": defect,
            "confidence": conf,
            "assigned_lot": lot,
        },
        "yield_summary": {
            "yield_percent": yield_pct,
            "good_dies": good,
            "fail_dies": fail,
            "total_dies": len(dies),
        },
        "grid_info": {
            "mode": grid_mode,
            "rows": rows,
            "columns": cols,
            "size": rows,
            "pitch": round(pitch, 3),
            "offset_x": 0,
            "offset_y": 0,
        },
        "wafer_geometry": {
            "center_x": IMG_SIZE / 2,
            "center_y": IMG_SIZE / 2,
            "radius": IMG_SIZE / 2 - 2,
        },
        "dies": dies,
        "visualization": _visualization(dies, pitch),
        "images": {
            "original": image_b64,
            "overlay": None,
            "density": None,
            "gradcam": None,
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
                )
                if clusters
                else "Low",
            },
            "clusters": clusters,
            "zone_analysis": {"zones": zones},
        },
        "mode": "render-demo",
        "taxonomy": [{"defect": d, "lot": DEFECT_TO_LOT[d]} for d in DEFECT_CLASSES],
    }


@app.get("/")
@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "wafervision-ai",
        "mode": "render-demo",
        "classes": list(DEFECT_CLASSES),
        "predict": "/predict",
        "docs": "/docs",
    }


@app.post("/predict")
@app.post("/analyze")
async def predict(
    image: UploadFile = File(...),
    grid_mode: str = Form("automatic"),
    grid_size: str | None = Form(None),
    include_images: str | None = Form(None),
) -> dict[str, Any]:
    raw = await image.read()
    name = image.filename or "wafer.bin"
    b64 = base64.b64encode(raw).decode("ascii") if raw else None
    size = int(grid_size) if grid_size else None
    return _analyze(name, grid_mode or "automatic", size, b64)


@app.post("/predict/batch")
async def predict_batch(
    images: list[UploadFile] = File(...),
    grid_mode: str = Form("automatic"),
    grid_size: str | None = Form(None),
) -> list[dict[str, Any]]:
    size = int(grid_size) if grid_size else None
    out: list[dict[str, Any]] = []
    for upload in images:
        raw = await upload.read()
        name = upload.filename or "wafer.bin"
        b64 = base64.b64encode(raw).decode("ascii") if raw else None
        out.append(_analyze(name, grid_mode or "automatic", size, b64))
    return out
