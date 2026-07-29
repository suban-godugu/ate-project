"""
Wafer die extraction, grid analysis, and yield analysis for WaferVision-AI.

Responsibility: convert a 224×224 wafer image into die-level manufacturing
analytics (geometry, grid, GOOD/FAIL dies, yield).

This module is the SINGLE SOURCE OF TRUTH for grid detection, die extraction,
and yield. It does NOT run CNN prediction — callers must pass the result from
``predict.py``.

Downstream consumers (pipeline, overlay, density, clusters, zones, API) must
reuse this module instead of recomputing die logic.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2
import numpy as np
from PIL import Image

from .preprocess import (
    apply_wafer_mask as _preprocess_apply_wafer_mask,
    create_wafer_mask,
    resize_rgb_to_img_size,
)
from .wafer_constants import (
    CENTER_X,
    CENTER_Y,
    IMG_SIZE,
    WAFER_RADIUS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Die fail determination (single source of truth — do not duplicate elsewhere)
# ---------------------------------------------------------------------------
# A die is FAIL when the fraction of "defect-like" pixels inside its cell
# (and inside the wafer mask) exceeds FAIL_PIXEL_RATIO.
# Defect-like pixels are those brighter than an adaptive threshold computed
# on the masked wafer grayscale (Otsu, with a safe fallback).
# Die cell must be clearly defect-colored (not a grazing edge hit).
FAIL_PIXEL_RATIO: float = 0.28
MIN_DIE_PIXELS: int = 4
# Coarse search bounds are derived from wafer radius (never a fixed grid size).
# Kept only as absolute safety clamps for pathological images.
_AUTO_PITCH_ABS_MIN: int = 3
_AUTO_PITCH_ABS_MAX: int = 32


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class DieAnalysisError(Exception):
    """Base exception for die / grid / yield analysis failures."""


class InvalidWaferImageError(DieAnalysisError):
    """Raised when the input wafer image is invalid."""


class GridDetectionError(DieAnalysisError):
    """Raised when automatic or manual grid detection fails."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WaferGeometry:
    """Circular wafer geometry in image coordinates."""

    center_x: float
    center_y: float
    radius: float

    @property
    def diameter(self) -> float:
        return float(self.radius * 2.0)

    def to_dict(self) -> dict[str, float]:
        return {
            "center_x": round(self.center_x, 4),
            "center_y": round(self.center_y, 4),
            "radius": round(self.radius, 4),
            "diameter": round(self.diameter, 4),
        }


@dataclass(frozen=True)
class GridInfo:
    """Detected or manually configured die grid."""

    mode: str
    pitch: float
    offset_x: float
    offset_y: float
    rows: int
    columns: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "pitch": round(float(self.pitch), 4),
            "offset_x": round(float(self.offset_x), 4),
            "offset_y": round(float(self.offset_y), 4),
            "rows": int(self.rows),
            "columns": int(self.columns),
        }


# ---------------------------------------------------------------------------
# Image loading / validation
# ---------------------------------------------------------------------------


def _to_rgb_array(image: str | Path | Image.Image | np.ndarray) -> np.ndarray:
    """Convert supported inputs to a contiguous uint8 RGB array."""
    if isinstance(image, np.ndarray):
        array = image
        if array.size == 0:
            raise InvalidWaferImageError("Empty numpy wafer image.")
        if array.ndim != 3 or array.shape[2] != 3:
            raise InvalidWaferImageError(
                f"Expected RGB array (H, W, 3); got shape={array.shape}."
            )
        if array.dtype != np.uint8:
            array = np.clip(array, 0, 255).astype(np.uint8)
        return np.ascontiguousarray(array)

    if isinstance(image, Image.Image):
        pil = image.convert("RGB")
    elif isinstance(image, (str, Path)):
        path = Path(image)
        if not path.is_file():
            raise InvalidWaferImageError(f"Wafer image not found: {path}")
        try:
            with Image.open(path) as handle:
                pil = handle.convert("RGB")
        except OSError as exc:
            raise InvalidWaferImageError(f"Corrupted wafer image: {path}") from exc
    else:
        raise InvalidWaferImageError(
            f"Unsupported image type: {type(image)!r}. "
            "Expected path, PIL.Image, or numpy.ndarray."
        )

    if pil.size[0] <= 0 or pil.size[1] <= 0:
        raise InvalidWaferImageError(f"Empty wafer image size: {pil.size}.")
    return np.asarray(pil, dtype=np.uint8)


def _ensure_analysis_resolution(rgb: np.ndarray) -> np.ndarray:
    """
    Ensure a square ``IMG_SIZE`` RGB image for die analysis.

    Uses the same bilinear resize as Grad-CAM / display so die x,y map 1:1
    onto Overlay, Density, and Grad-CAM panels.
    """
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise InvalidWaferImageError(f"Expected RGB image; got shape={rgb.shape}.")
    height, width = int(rgb.shape[0]), int(rgb.shape[1])
    if height <= 0 or width <= 0:
        raise InvalidWaferImageError("Empty wafer image.")
    try:
        return resize_rgb_to_img_size(rgb)
    except Exception as exc:  # noqa: BLE001
        raise InvalidWaferImageError(str(exc)) from exc


def _to_gray(rgb: np.ndarray) -> np.ndarray:
    """Convert RGB uint8 image to grayscale float32."""
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)


# ---------------------------------------------------------------------------
# Mask & geometry
# ---------------------------------------------------------------------------


def apply_wafer_mask(
    image: np.ndarray,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Apply the circular wafer mask (pixels outside → black).

    Reuses ``preprocess.create_wafer_mask`` / ``apply_wafer_mask`` so masking
    stays consistent with the rest of the platform.
    """
    rgb = _ensure_analysis_resolution(_to_rgb_array(image)) if image.ndim == 3 else image
    if mask is None:
        mask = create_wafer_mask(size=int(rgb.shape[0]))
    masked = _preprocess_apply_wafer_mask(rgb, mask)
    if not isinstance(masked, np.ndarray):
        raise DieAnalysisError("Wafer mask application did not return a numpy array.")
    return masked


def estimate_wafer_geometry(
    image: np.ndarray | None = None,
    *,
    size: int = IMG_SIZE,
) -> WaferGeometry:
    """
    Estimate wafer center / radius / diameter.

    Uses ``wafer_constants`` as the canonical geometry for ``IMG_SIZE`` images.
    When a non-standard size is requested, values are scaled proportionally.
    Optional ``image`` is validated but geometry remains deterministic unless
    the image reveals a tighter illuminated circle (refined estimate).
    """
    scale = float(size) / float(IMG_SIZE)
    geometry = WaferGeometry(
        center_x=CENTER_X * scale,
        center_y=CENTER_Y * scale,
        radius=WAFER_RADIUS * scale,
    )

    if image is None:
        return geometry

    rgb = _ensure_analysis_resolution(_to_rgb_array(image))
    gray = _to_gray(rgb)
    # Refine radius from illuminated content when possible
    _, binary = cv2.threshold(
        gray.astype(np.uint8),
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    ys, xs = np.where(binary > 0)
    if xs.size < 50:
        return geometry

    # Minimum enclosing circle of illuminated pixels
    points = np.column_stack((xs.astype(np.float32), ys.astype(np.float32)))
    (cx, cy), radius = cv2.minEnclosingCircle(points)
    # Keep refinement inside a sane band relative to constants
    const_radius = WAFER_RADIUS * (rgb.shape[0] / float(IMG_SIZE))
    if 0.55 * const_radius <= radius <= 1.05 * const_radius:
        return WaferGeometry(center_x=float(cx), center_y=float(cy), radius=float(radius))
    return WaferGeometry(
        center_x=CENTER_X * (rgb.shape[0] / float(IMG_SIZE)),
        center_y=CENTER_Y * (rgb.shape[0] / float(IMG_SIZE)),
        radius=float(const_radius),
    )


# ---------------------------------------------------------------------------
# Grid detection
# ---------------------------------------------------------------------------


def _pitch_search_range(geometry: WaferGeometry) -> tuple[int, int]:
    """
    Adaptive pitch search window from wafer radius (no hardcoded grid size).

    Allows roughly 14–70 dies across the wafer diameter.
    """
    diameter = max(float(geometry.diameter), 1.0)
    pitch_min = max(_AUTO_PITCH_ABS_MIN, int(np.floor(diameter / 70.0)))
    pitch_max = min(
        _AUTO_PITCH_ABS_MAX,
        max(pitch_min + 1, int(np.ceil(diameter / 20.0))),
    )
    return int(pitch_min), int(pitch_max)


def _structure_map(gray_masked: np.ndarray) -> np.ndarray:
    """
    Color-agnostic die-boundary energy map.

    Combines morphological gradient with separable Sobel responses so
    detection does not depend on a specific defect colour.
    """
    blur = cv2.GaussianBlur(gray_masked, (3, 3), 0)
    u8 = np.clip(blur, 0, 255).astype(np.uint8)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph = cv2.morphologyEx(u8, cv2.MORPH_GRADIENT, kernel).astype(np.float32)
    sobel_x = np.abs(cv2.Sobel(blur, cv2.CV_32F, 1, 0, ksize=3))
    sobel_y = np.abs(cv2.Sobel(blur, cv2.CV_32F, 0, 1, ksize=3))
    return morph + 0.5 * (sobel_x + sobel_y)


def _central_roi_bounds(
    geometry: WaferGeometry,
    height: int,
    width: int,
    *,
    fraction: float = 0.55,
) -> tuple[int, int, int, int]:
    """Axis-aligned ROI covering the central wafer disk (for stable pitch)."""
    half = max(2.0, float(geometry.radius) * float(fraction))
    x0 = int(max(0, np.floor(geometry.center_x - half)))
    y0 = int(max(0, np.floor(geometry.center_y - half)))
    x1 = int(min(width, np.ceil(geometry.center_x + half)))
    y1 = int(min(height, np.ceil(geometry.center_y + half)))
    if x1 - x0 < 4 or y1 - y0 < 4:
        return 0, 0, width, height
    return x0, y0, x1, y1


def _estimate_coarse_pitches(
    structure: np.ndarray,
    geometry: WaferGeometry,
) -> tuple[float, float]:
    """
    Estimate a single coarse lattice pitch from wafer radius (adaptive prior).

    Autocorrelation is consulted only as a soft corroboration log; the lattice
    seed itself stays on the geometric prior so same-layout wafers share one
    candidate grid. Multi-reference measurements refine the final pitch later.
    """
    pitch_min, pitch_max = _pitch_search_range(geometry)
    diameter = max(float(geometry.diameter), 1.0)
    prior = float(np.clip(diameter / 50.0, pitch_min, pitch_max))

    # Soft check — logged only; does not move the seed
    seeds = _coarse_pitch_seeds(structure, geometry)
    if seeds:
        autocorr = float(seeds[0])
        if abs(autocorr - prior) > 0.35 * prior:
            logger.debug(
                "Autocorr pitch %.2f diverges from geometric prior %.2f; "
                "keeping prior for candidate lattice.",
                autocorr,
                prior,
            )

    return prior, prior


def _coarse_pitch_seeds(
    structure: np.ndarray,
    geometry: WaferGeometry,
) -> list[float]:
    """Ranked coarse pitch seeds (strongest autocorrelation first)."""
    height, width = structure.shape
    x0, y0, x1, y1 = _central_roi_bounds(geometry, height, width)
    roi = structure[y0:y1, x0:x1]
    pitch_min, pitch_max = _pitch_search_range(geometry)

    yy, xx = np.ogrid[y0:y1, x0:x1]
    dist2 = (xx - geometry.center_x) ** 2 + (yy - geometry.center_y) ** 2
    roi_mask = dist2 <= (geometry.radius * 0.55) ** 2
    if int(roi_mask.sum()) < 64:
        roi_mask = np.ones_like(roi, dtype=bool)

    row_proj = np.zeros(roi.shape[0], dtype=np.float64)
    col_proj = np.zeros(roi.shape[1], dtype=np.float64)
    for i in range(roi.shape[0]):
        vals = roi[i, roi_mask[i]]
        row_proj[i] = float(vals.mean()) if vals.size else 0.0
    for j in range(roi.shape[1]):
        vals = roi[roi_mask[:, j], j]
        col_proj[j] = float(vals.mean()) if vals.size else 0.0

    peaks_x = _autocorr_pitch_peaks(col_proj, pitch_min, pitch_max, top_k=3)
    peaks_y = _autocorr_pitch_peaks(row_proj, pitch_min, pitch_max, top_k=3)
    pitch_2d = _autocorr_pitch_2d(roi, roi_mask, pitch_min, pitch_max)

    diameter = max(float(geometry.diameter), 1.0)
    fallback = float(np.clip(diameter / 50.0, pitch_min, pitch_max))

    # Require a clearly periodic structure; otherwise use radius-derived fallback
    strong: list[tuple[float, float]] = []  # (neg_strength, pitch)
    for strength, lag in peaks_x + peaks_y:
        if strength >= 0.08:
            strong.append((-strength, float(lag)))
    if pitch_2d is not None and strong:
        strong.append((-0.1, float(pitch_2d)))

    if not strong:
        return [fallback]

    strong.sort()
    fundamentals: list[float] = []
    for _, p in strong:
        if any(abs(p - 2.0 * f) <= 0.3 * f for f in fundamentals):
            continue
        replaced = False
        for i, f in enumerate(fundamentals):
            if abs(f - 2.0 * p) <= 0.3 * p:
                fundamentals[i] = p
                replaced = True
                break
        if not replaced:
            fundamentals.append(p)

    ordered: list[float] = []
    for _, pitch in strong:
        mapped = min(fundamentals, key=lambda f: abs(f - pitch)) if fundamentals else pitch
        if mapped < pitch_min or mapped > pitch_max:
            continue
        if any(abs(mapped - existing) <= 0.2 * existing for existing in ordered):
            continue
        ordered.append(float(mapped))

    return ordered if ordered else [fallback]


def _autocorr_pitch_peaks(
    signal: np.ndarray,
    pitch_min: int,
    pitch_max: int,
    *,
    top_k: int = 3,
) -> list[tuple[float, float]]:
    """Return up to ``top_k`` (strength, lag) autocorrelation peaks."""
    if signal.size < pitch_min * 2:
        return []
    centered = signal - float(signal.mean())
    if float(np.std(centered)) < 1e-6:
        return []
    corr = np.correlate(centered, centered, mode="full")
    corr = corr[corr.size // 2 :]
    lo = max(pitch_min, 1)
    hi = min(pitch_max, corr.size - 2)
    if hi <= lo:
        return []

    window = corr[lo : hi + 1]
    lag0 = float(corr[0]) if corr.size and corr[0] > 0 else 1.0
    peaks: list[tuple[float, float]] = []
    for i in range(1, window.size - 1):
        if window[i] >= window[i - 1] and window[i] >= window[i + 1] and window[i] > 0:
            lag = float(lo + i)
            strength = float(window[i]) / lag0
            if strength < 0.05:
                continue
            y0, y1, y2 = float(window[i - 1]), float(window[i]), float(window[i + 1])
            denom = y0 - 2.0 * y1 + y2
            if abs(denom) > 1e-12:
                delta = float(np.clip(0.5 * (y0 - y2) / denom, -0.5, 0.5))
                lag += delta
            peaks.append((strength, lag))

    peaks.sort(key=lambda t: t[0], reverse=True)
    return peaks[:top_k]


def _autocorr_pitch_2d(
    roi: np.ndarray,
    roi_mask: np.ndarray,
    pitch_min: int,
    pitch_max: int,
) -> float | None:
    """Estimate isotropic pitch from 2-D autocorrelation radial peak."""
    if roi.size < 64:
        return None
    work = roi.astype(np.float64).copy()
    work[~roi_mask] = float(work[roi_mask].mean()) if roi_mask.any() else 0.0
    work -= work.mean()
    if float(work.std()) < 1e-6:
        return None

    # FFT-based autocorrelation
    f = np.fft.rfft2(work)
    corr = np.fft.irfft2(f * np.conj(f), s=work.shape)
    corr = np.fft.fftshift(corr)
    cy, cx = corr.shape[0] // 2, corr.shape[1] // 2

    best_lag = None
    best_val = -1e18
    # Search annular band of lags
    for dy in range(-pitch_max, pitch_max + 1):
        for dx in range(-pitch_max, pitch_max + 1):
            lag = float(np.hypot(dx, dy))
            if lag < pitch_min or lag > pitch_max:
                continue
            val = float(corr[cy + dy, cx + dx])
            if val > best_val:
                best_val = val
                best_lag = lag
    if best_lag is None or best_val <= 0:
        return None
    return float(best_lag)


def _die_fully_inside(
    cx: float,
    cy: float,
    half_w: float,
    half_h: float,
    geometry: WaferGeometry,
    *,
    margin: float = 0.5,
) -> bool:
    """True when the die rectangle lies fully inside the wafer circle."""
    corners = (
        (cx - half_w, cy - half_h),
        (cx + half_w, cy - half_h),
        (cx - half_w, cy + half_h),
        (cx + half_w, cy + half_h),
    )
    radius = max(0.0, geometry.radius - margin)
    for x, y in corners:
        dx = x - geometry.center_x
        dy = y - geometry.center_y
        if dx * dx + dy * dy > radius * radius:
            return False
    return True


def _perimeter_clarity(
    structure: np.ndarray,
    cx: float,
    cy: float,
    half_w: float,
    half_h: float,
) -> float:
    """Mean structure energy on the die perimeter vs interior (higher = clearer)."""
    height, width = structure.shape
    x0 = int(max(0, np.floor(cx - half_w)))
    y0 = int(max(0, np.floor(cy - half_h)))
    x1 = int(min(width, np.ceil(cx + half_w)))
    y1 = int(min(height, np.ceil(cy + half_h)))
    if x1 - x0 < 3 or y1 - y0 < 3:
        return -1e9

    cell = structure[y0:y1, x0:x1]
    if cell.size < 9:
        return -1e9
    # Perimeter ring (1 px) vs eroded interior
    ring = cell.copy()
    if cell.shape[0] > 2 and cell.shape[1] > 2:
        interior = cell[1:-1, 1:-1]
        ring[1:-1, 1:-1] = 0.0
        peri = float(ring.mean()) if ring.size else 0.0
        inside = float(interior.mean()) if interior.size else 0.0
    else:
        peri = float(cell.mean())
        inside = peri
    return peri - 0.35 * inside


def _mad_inliers(values: Sequence[float], *, z_thresh: float = 3.0) -> list[float]:
    """
    Keep values within ``z_thresh`` modified Z-scores of the median (MAD filter).

    Falls back to IQR fences when MAD is near zero.
    """
    arr = np.asarray([float(v) for v in values if v is not None], dtype=np.float64)
    if arr.size == 0:
        return []
    if arr.size < 3:
        return [float(v) for v in arr]

    med = float(np.median(arr))
    mad = float(np.median(np.abs(arr - med)))
    if mad > 1e-9:
        # Consistency constant 0.6745 maps MAD → σ for normal data
        z = 0.6745 * (arr - med) / mad
        kept = arr[np.abs(z) <= z_thresh]
        if kept.size >= max(2, arr.size // 4):
            return [float(v) for v in kept]

    # IQR fallback when MAD collapses (many identical samples)
    q1, q3 = np.percentile(arr, [25.0, 75.0])
    iqr = float(q3 - q1)
    if iqr <= 1e-9:
        return [float(v) for v in arr]
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    kept = arr[(arr >= lo) & (arr <= hi)]
    return [float(v) for v in kept] if kept.size else [float(v) for v in arr]


@dataclass(frozen=True)
class _DieMeasurement:
    """Per-candidate geometric measurement (automatic grid only)."""

    cx: float
    cy: float
    width: float
    height: float
    pitch_x: float
    pitch_y: float
    score: float
    seed: float = 0.0


def _defect_interference(
    gray: np.ndarray,
    mask: np.ndarray,
    cx: float,
    cy: float,
    half_w: float,
    half_h: float,
    wafer_median: float,
) -> float:
    """
    Higher = more defect-like content inside the die (colour-agnostic intensity).

    Bright outliers relative to the wafer median indicate defect interference.
    """
    height, width = gray.shape
    x0 = int(max(0, np.floor(cx - half_w)))
    y0 = int(max(0, np.floor(cy - half_h)))
    x1 = int(min(width, np.ceil(cx + half_w)))
    y1 = int(min(height, np.ceil(cy + half_h)))
    if x1 <= x0 or y1 <= y0:
        return 1e9

    cell = gray[y0:y1, x0:x1]
    cell_mask = mask[y0:y1, x0:x1] > 0.5
    if int(cell_mask.sum()) < MIN_DIE_PIXELS:
        return 1e9
    vals = cell[cell_mask]
    # Fraction of pixels well above wafer median (defect-like)
    bright = float((vals > wafer_median + 25.0).mean())
    contrast = float(vals.std())
    return bright + 0.002 * contrast


def _collect_candidate_dies(
    structure: np.ndarray,
    gray: np.ndarray,
    mask: np.ndarray,
    geometry: WaferGeometry,
    pitch_x: float,
    pitch_y: float,
) -> list[tuple[float, float, float]]:
    """
    Collect high-quality candidate dies near the wafer centre.

    Returns list of (cx, cy, score). Count is determined dynamically from
    available quality (target band ~20–100; never hardcoded as a fixed N).
    """
    half_w = pitch_x / 2.0
    half_h = pitch_y / 2.0
    if half_w < 0.75 or half_h < 0.75:
        return []

    wafer_pixels = gray[mask > 0.5]
    wafer_median = float(np.median(wafer_pixels)) if wafer_pixels.size else 0.0

    # Search radius grows with available interior (no fixed grid size)
    step = min(pitch_x, pitch_y)
    max_steps = int(max(3, np.floor((geometry.radius * 0.65 - max(half_w, half_h)) / step)))

    strict: list[tuple[float, float, float]] = []
    relaxed: list[tuple[float, float, float]] = []

    for row in range(-max_steps, max_steps + 1):
        for col in range(-max_steps, max_steps + 1):
            cx = geometry.center_x + col * pitch_x
            cy = geometry.center_y + row * pitch_y
            if not _die_fully_inside(cx, cy, half_w, half_h, geometry):
                continue

            neighbours = (
                (cx - pitch_x, cy),
                (cx + pitch_x, cy),
                (cx, cy - pitch_y),
                (cx, cy + pitch_y),
            )
            surrounded = all(
                _die_fully_inside(nx, ny, half_w, half_h, geometry)
                for nx, ny in neighbours
            )

            clarity = _perimeter_clarity(structure, cx, cy, half_w, half_h)
            if clarity < -1e8:
                continue
            interference = _defect_interference(
                gray, mask, cx, cy, half_w, half_h, wafer_median
            )
            dist = float(np.hypot(cx - geometry.center_x, cy - geometry.center_y))
            # Prefer clear boundaries, low defect interference, near centre
            score = clarity - 8.0 * interference - 0.015 * dist

            if surrounded:
                strict.append((score, cx, cy))
            else:
                relaxed.append((score, cx, cy))

    pool = strict if strict else relaxed
    if not pool:
        return []

    pool.sort(key=lambda t: t[0], reverse=True)

    # Dynamic keep count from score distribution (adaptive 20–100 band)
    scores = np.asarray([t[0] for t in pool], dtype=np.float64)
    med_score = float(np.median(scores))
    # Keep candidates at or above median quality among the pool
    quality = [t for t in pool if t[0] >= med_score - 1e-9]
    if len(quality) < 20 and len(pool) >= 20:
        quality = pool[: max(20, len(pool) // 2)]
    elif len(quality) < 20:
        quality = list(pool)

    # Cap at 100 best; floor is whatever quality provides (may be < 20 on sparse wafers)
    quality = quality[:100]
    return [(float(cx), float(cy), float(score)) for score, cx, cy in quality]


def _measure_axis_extent(
    structure: np.ndarray,
    center: float,
    orthogonal: float,
    *,
    axis: str,
    search: float,
) -> tuple[float, float] | None:
    """
    Measure die edge locations along one axis around a candidate centre.

    Returns (negative_extent, positive_extent) from centre to opposing edges,
    or None when peaks cannot be resolved.
    """
    height, width = structure.shape
    search = max(2.0, float(search))
    if axis == "x":
        y = int(np.clip(round(orthogonal), 0, height - 1))
        y0 = max(0, y - 1)
        y1 = min(height, y + 2)
        profile = structure[y0:y1, :].mean(axis=0)
        c = float(center)
        lo = int(max(0, np.floor(c - search)))
        hi = int(min(width - 1, np.ceil(c + search)))
    else:
        x = int(np.clip(round(orthogonal), 0, width - 1))
        x0 = max(0, x - 1)
        x1 = min(width, x + 2)
        profile = structure[:, x0:x1].mean(axis=1)
        c = float(center)
        lo = int(max(0, np.floor(c - search)))
        hi = int(min(height - 1, np.ceil(c + search)))

    if hi - lo < 4:
        return None

    segment = profile[lo : hi + 1]
    peaks: list[tuple[int, float]] = []
    for i in range(1, segment.size - 1):
        if segment[i] >= segment[i - 1] and segment[i] >= segment[i + 1]:
            peaks.append((lo + i, float(segment[i])))
    if len(peaks) < 2:
        return None

    left = [(p, v) for p, v in peaks if p < c - 0.5]
    right = [(p, v) for p, v in peaks if p > c + 0.5]
    if not left or not right:
        return None
    left_pos = max(left, key=lambda t: t[1])[0]
    right_pos = max(right, key=lambda t: t[1])[0]
    neg = c - float(left_pos)
    pos = float(right_pos) - c
    if neg < 0.75 or pos < 0.75:
        return None
    return neg, pos


def _neighbour_pitch(
    structure: np.ndarray,
    ref_x: float,
    ref_y: float,
    *,
    axis: str,
    expected: float,
) -> float | None:
    """Estimate centre-to-centre pitch from the nearest neighbour along an axis."""
    height, width = structure.shape
    expected = max(float(expected), 2.0)
    half = expected * 0.35

    if axis == "x":
        y0 = int(max(0, np.floor(ref_y - half)))
        y1 = int(min(height, np.ceil(ref_y + half)))
        profile = (
            structure[y0:y1, :].mean(axis=0) if y1 > y0 else structure.mean(axis=0)
        )
        center = ref_x
        limit = width
    else:
        x0 = int(max(0, np.floor(ref_x - half)))
        x1 = int(min(width, np.ceil(ref_x + half)))
        profile = (
            structure[:, x0:x1].mean(axis=1) if x1 > x0 else structure.mean(axis=1)
        )
        center = ref_y
        limit = height

    spacings: list[float] = []
    for direction in (-1.0, 1.0):
        target = center + direction * expected
        lo = int(max(0, np.floor(target - expected * 0.35)))
        hi = int(min(limit - 1, np.ceil(target + expected * 0.35)))
        if hi <= lo:
            continue
        window = profile[lo : hi + 1]
        idx = int(np.argmin(window)) + lo
        spacings.append(abs(float(idx) - center))

    if not spacings:
        return None
    return float(np.median(spacings))


def _measure_candidate(
    structure: np.ndarray,
    cx: float,
    cy: float,
    coarse_pitch_x: float,
    coarse_pitch_y: float,
    score: float,
) -> _DieMeasurement | None:
    """Measure one candidate; return None if edges/pitches cannot be resolved."""
    search_x = max(coarse_pitch_x * 1.25, coarse_pitch_x + 1.0)
    search_y = max(coarse_pitch_y * 1.25, coarse_pitch_y + 1.0)

    extent_x = _measure_axis_extent(structure, cx, cy, axis="x", search=search_x)
    extent_y = _measure_axis_extent(structure, cy, cx, axis="y", search=search_y)
    if extent_x is None or extent_y is None:
        return None

    width = float(extent_x[0] + extent_x[1])
    height = float(extent_y[0] + extent_y[1])
    if width < 1.0 or height < 1.0:
        return None

    pitch_x = _neighbour_pitch(
        structure, cx, cy, axis="x", expected=coarse_pitch_x
    )
    pitch_y = _neighbour_pitch(
        structure, cx, cy, axis="y", expected=coarse_pitch_y
    )
    if pitch_x is None:
        pitch_x = width
    if pitch_y is None:
        pitch_y = height

    # Drop pathological ratios vs coarse estimate (gross failures)
    if not (0.45 * coarse_pitch_x <= pitch_x <= 1.8 * coarse_pitch_x):
        return None
    if not (0.45 * coarse_pitch_y <= pitch_y <= 1.8 * coarse_pitch_y):
        return None
    if not (0.4 * pitch_x <= width <= 1.35 * pitch_x):
        return None
    if not (0.4 * pitch_y <= height <= 1.35 * pitch_y):
        return None

    seed = 0.5 * (float(coarse_pitch_x) + float(coarse_pitch_y))
    return _DieMeasurement(
        cx=float(cx),
        cy=float(cy),
        width=float(width),
        height=float(height),
        pitch_x=float(pitch_x),
        pitch_y=float(pitch_y),
        score=float(score),
        seed=float(seed),
    )


def detect_grid(
    image: np.ndarray,
    geometry: WaferGeometry | None = None,
    *,
    mode: str = "automatic",
    grid_size: int | None = None,
) -> GridInfo:
    """
    Detect or construct the die grid.

    Automatic mode uses multi-reference die estimation (robust median geometry)
    and replicates one lattice across the wafer. Manual mode accepts
    ``grid_size`` as square rows=columns and derives pitch / offsets from
    wafer geometry.
    """
    rgb = _ensure_analysis_resolution(_to_rgb_array(image))
    masked = apply_wafer_mask(rgb)
    geometry = geometry or estimate_wafer_geometry(masked)
    normalized_mode = mode.strip().lower()

    if normalized_mode in {"manual", "custom"}:
        if grid_size is None or int(grid_size) < 2:
            raise GridDetectionError(
                f"Manual grid requires grid_size >= 2; got {grid_size}."
            )
        return _manual_grid(geometry, int(grid_size))

    if normalized_mode not in {"automatic", "auto"}:
        raise GridDetectionError(
            f"Unknown grid mode '{mode}'. Expected 'automatic' or 'manual'."
        )

    return _automatic_grid(masked, geometry)


def _manual_grid(geometry: WaferGeometry, grid_size: int) -> GridInfo:
    """Build a centered square grid from a user-provided grid size."""
    pitch = (2.0 * geometry.radius) / float(grid_size)
    if pitch < 1.0:
        raise GridDetectionError(
            f"Manual grid_size={grid_size} produces pitch < 1px for this wafer."
        )
    # First die center at (center - radius + pitch/2)
    offset_x = geometry.center_x - geometry.radius + pitch / 2.0
    offset_y = geometry.center_y - geometry.radius + pitch / 2.0
    return GridInfo(
        mode="manual",
        pitch=float(pitch),
        offset_x=float(offset_x),
        offset_y=float(offset_y),
        rows=int(grid_size),
        columns=int(grid_size),
    )


def _count_dies_in_grid(grid: GridInfo, geometry: WaferGeometry) -> int:
    """Count cells whose centres fall inside the wafer (matches extraction clip)."""
    pitch = float(grid.pitch)
    half = pitch / 2.0
    count = 0
    for row in range(int(grid.rows)):
        for column in range(int(grid.columns)):
            cx = float(grid.offset_x) + column * pitch
            cy = float(grid.offset_y) + row * pitch
            if _die_center_inside(cx, cy, geometry, margin=half * 0.25):
                count += 1
    return count


def _automatic_grid(masked_rgb: np.ndarray, geometry: WaferGeometry) -> GridInfo:
    """
    Automatic grid via multi-reference die estimation.

    Steps:
      1–2. Canonical wafer centre / radius for a stable lattice frame.
      3–5. Collect many high-quality central candidates (adaptive ~20–100).
      6. Measure width / height / pitches per candidate.
      7–8. MAD/IQR reject outliers; take robust medians.
      9. Quantize to integer dies across the diameter; replicate once.
     10. Outer cells clipped later by centre-in-circle extraction.
    """
    t0 = time.perf_counter()

    # Shared mask geometry → same lattice frame for every IMG_SIZE wafer.
    scale = float(masked_rgb.shape[0]) / float(IMG_SIZE)
    lattice_geometry = WaferGeometry(
        center_x=CENTER_X * scale,
        center_y=CENTER_Y * scale,
        radius=WAFER_RADIUS * scale,
    )
    _ = geometry

    gray = _to_gray(masked_rgb)
    mask = create_wafer_mask(size=int(gray.shape[0]))
    gray_masked = gray * mask
    structure = _structure_map(gray_masked)

    coarse_x, coarse_y = _estimate_coarse_pitches(structure, lattice_geometry)
    candidates = _collect_candidate_dies(
        structure, gray_masked, mask, lattice_geometry, coarse_x, coarse_y
    )

    measurements: list[_DieMeasurement] = []
    measure_failures = 0
    for cx, cy, score in candidates:
        measured = _measure_candidate(
            structure, cx, cy, coarse_x, coarse_y, score
        )
        if measured is None:
            measure_failures += 1
            continue
        measurements.append(measured)

    rejected = 0
    if measurements:
        before = len(measurements)
        widths = [m.width for m in measurements]
        heights = [m.height for m in measurements]
        pitches_x = [m.pitch_x for m in measurements]
        pitches_y = [m.pitch_y for m in measurements]

        w_in = np.asarray(_mad_inliers(widths), dtype=np.float64)
        h_in = np.asarray(_mad_inliers(heights), dtype=np.float64)
        px_in = np.asarray(_mad_inliers(pitches_x), dtype=np.float64)
        py_in = np.asarray(_mad_inliers(pitches_y), dtype=np.float64)

        w_med = float(np.median(w_in)) if w_in.size else float(np.median(widths))
        h_med = float(np.median(h_in)) if h_in.size else float(np.median(heights))
        px_med = float(np.median(px_in)) if px_in.size else float(np.median(pitches_x))
        py_med = float(np.median(py_in)) if py_in.size else float(np.median(pitches_y))

        def _axis_tol(samples: np.ndarray, med: float) -> float:
            if samples.size == 0:
                return max(0.5, 0.25 * abs(med))
            mad = float(np.median(np.abs(samples - med)))
            if mad < 1e-9:
                return max(0.5, 0.12 * abs(med))
            return max(0.35, 2.5 * mad / 0.6745)

        filtered = [
            m
            for m in measurements
            if abs(m.width - w_med) <= _axis_tol(w_in, w_med)
            and abs(m.height - h_med) <= _axis_tol(h_in, h_med)
            and abs(m.pitch_x - px_med) <= _axis_tol(px_in, px_med)
            and abs(m.pitch_y - py_med) <= _axis_tol(py_in, py_med)
        ]

        rejected = before - len(filtered) + measure_failures
        if len(filtered) < max(5, before // 5):
            filtered = measurements
            rejected = measure_failures

        median_width = float(np.median([m.width for m in filtered]))
        median_height = float(np.median([m.height for m in filtered]))
        median_pitch_x = float(np.median([m.pitch_x for m in filtered]))
        median_pitch_y = float(np.median([m.pitch_y for m in filtered]))
        candidates_used = len(filtered)

        pitch_samples = np.asarray(
            [0.5 * (m.pitch_x + m.pitch_y) for m in filtered], dtype=np.float64
        )
        med_p = float(np.median(pitch_samples))
        pitch_mad = float(np.median(np.abs(pitch_samples - med_p)))
        coarse_mid = 0.5 * (coarse_x + coarse_y)
        rel_mad = pitch_mad / max(med_p, 1.0)
        rel_shift = abs(med_p - coarse_mid) / max(coarse_mid, 1.0)

        # Default: keep geometric prior (layout-stable). Accept a different
        # measured pitch only with strong multi-ref evidence of a new layout.
        # Do NOT mildly blend near-prior measurements — small biases flip
        # round(diameter/pitch) and break same-layout consistency.
        if candidates_used >= 40 and rel_mad <= 0.06 and rel_shift > 0.35:
            pass  # keep measured medians (clearly different layout)
        else:
            median_pitch_x = float(coarse_x)
            median_pitch_y = float(coarse_y)
    else:
        logger.warning(
            "Multi-reference measurement failed (%d candidates); "
            "using coarse pitches pitch_x=%.2f pitch_y=%.2f.",
            len(candidates),
            coarse_x,
            coarse_y,
        )
        median_width = float(coarse_x)
        median_height = float(coarse_y)
        median_pitch_x = float(coarse_x)
        median_pitch_y = float(coarse_y)
        candidates_used = 0
        rejected = measure_failures + len(candidates)

    if abs(median_pitch_x - median_pitch_y) <= 0.15 * max(median_pitch_x, median_pitch_y):
        raw_pitch = 0.5 * (median_pitch_x + median_pitch_y)
    else:
        raw_pitch = float(np.median([median_pitch_x, median_pitch_y]))

    if raw_pitch < 1.0:
        raise GridDetectionError("Automatic grid detection produced invalid pitch.")

    # Quantize in die-count space for layout-stable rows/pitch/coordinates
    diameter = float(lattice_geometry.diameter)
    n_across = max(2, int(round(diameter / raw_pitch)))
    pitch = diameter / float(n_across)
    rows = columns = int(n_across)

    span = (columns - 1) * pitch
    offset_x = lattice_geometry.center_x - span / 2.0
    offset_y = lattice_geometry.center_y - span / 2.0

    grid = GridInfo(
        mode="automatic",
        pitch=float(pitch),
        offset_x=float(offset_x),
        offset_y=float(offset_y),
        rows=int(rows),
        columns=int(columns),
    )

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    total_dies = _count_dies_in_grid(grid, lattice_geometry)

    logger.info(
        "Reference Geometry\n"
        "Candidates Used              : %d\n"
        "Median Die Width             : %.4f\n"
        "Median Die Height            : %.4f\n"
        "Median Horizontal Pitch      : %.4f\n"
        "Median Vertical Pitch        : %.4f\n"
        "Final Grid                   : %d × %d\n"
        "Total Dies                   : %d\n"
        "Rejected Candidates          : %d\n"
        "Grid Generation Time         : %.2f",
        candidates_used,
        median_width,
        median_height,
        median_pitch_x,
        median_pitch_y,
        grid.rows,
        grid.columns,
        total_dies,
        rejected,
        elapsed_ms,
    )

    return grid


# ---------------------------------------------------------------------------
# Die status (GOOD / FAIL)
# ---------------------------------------------------------------------------


def _defect_color_mask(rgb: np.ndarray) -> np.ndarray:
    """
    Detect defect-colored pixels on wafer-map RGB images.

    WM811K-style maps encode FAIL as yellow/orange/red and GOOD as dark
    green/teal. Grayscale Otsu mislabels ~half the dies on these maps.
    """
    if rgb.ndim != 3 or rgb.shape[2] < 3:
        raise DieAnalysisError(f"Expected RGB for defect color mask; got {rgb.shape}.")
    r = rgb[:, :, 0].astype(np.float32)
    g = rgb[:, :, 1].astype(np.float32)
    b = rgb[:, :, 2].astype(np.float32)
    yellow_orange = (r > 100.0) & (g > 55.0) & (b < 150.0) & ((r + g) > (1.55 * b + 35.0))
    bright_fail = (r > 175.0) & (g > 140.0) & (b < 170.0)
    return yellow_orange | bright_fail


def _defect_threshold(gray: np.ndarray, mask: np.ndarray) -> float:
    """Adaptive defect intensity threshold on masked wafer pixels (grayscale fallback)."""
    pixels = gray[mask > 0.5]
    if pixels.size == 0:
        return 255.0
    pixels_u8 = np.clip(pixels, 0, 255).astype(np.uint8)
    threshold_value, _ = cv2.threshold(
        pixels_u8,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )
    # Guard against pathological Otsu results on near-uniform wafers
    median = float(np.median(pixels))
    return float(max(threshold_value, median + 15.0))


def _classify_die_status(
    gray: np.ndarray,
    mask: np.ndarray,
    bbox: tuple[int, int, int, int],
    threshold: float,
    *,
    rgb: np.ndarray | None = None,
    center: tuple[float, float] | None = None,
) -> str:
    """
    Classify one die cell as GOOD or FAIL.

    For colored wafer bin maps, prefer the die-center color (yellow/orange =
    FAIL). Cell ratio is a secondary check for partial coverage. Grayscale
    intensity is the fallback when ``rgb`` is absent.
    """
    x0, y0, x1, y1 = bbox
    if x1 <= x0 or y1 <= y0:
        return "GOOD"

    cell_mask = mask[y0:y1, x0:x1]
    valid = cell_mask > 0.5
    if int(valid.sum()) < MIN_DIE_PIXELS:
        return "GOOD"

    if rgb is not None:
        defect_full = _defect_color_mask(rgb)
        if center is not None:
            cx_i = int(round(center[0]))
            cy_i = int(round(center[1]))
            h, w = defect_full.shape
            if 0 <= cx_i < w and 0 <= cy_i < h and bool(defect_full[cy_i, cx_i]):
                return "FAIL"
            # 3×3 neighborhood majority around the die center (bin-map friendly)
            x_a = max(0, cx_i - 1)
            x_b = min(w, cx_i + 2)
            y_a = max(0, cy_i - 1)
            y_b = min(h, cy_i + 2)
            patch = defect_full[y_a:y_b, x_a:x_b]
            if patch.size and float(patch.mean()) >= 0.45:
                return "FAIL"

        cell_rgb = rgb[y0:y1, x0:x1]
        defect = _defect_color_mask(cell_rgb) & valid
        defect_ratio = float(defect.sum()) / float(valid.sum())
        # Strong cell coverage only — avoids marking dies that merely graze a fail
        return "FAIL" if defect_ratio >= max(FAIL_PIXEL_RATIO, 0.45) else "GOOD"

    cell_gray = gray[y0:y1, x0:x1]
    defect_ratio = float(((cell_gray > threshold) & valid).sum()) / float(valid.sum())
    return "FAIL" if defect_ratio >= FAIL_PIXEL_RATIO else "GOOD"


# ---------------------------------------------------------------------------
# Die extraction
# ---------------------------------------------------------------------------


def _die_center_inside(
    x: float,
    y: float,
    geometry: WaferGeometry,
    *,
    margin: float = 0.0,
) -> bool:
    """Return True if die center lies inside the wafer circle."""
    radius = max(0.0, geometry.radius - margin)
    dx = x - geometry.center_x
    dy = y - geometry.center_y
    return (dx * dx + dy * dy) <= (radius * radius)


def extract_dies(
    image: np.ndarray,
    grid: GridInfo,
    geometry: WaferGeometry | None = None,
) -> list[dict[str, Any]]:
    """
    Extract every die for an automatic (or already-built) grid.

    Each die includes die_id, row, column, x, y, bbox, and status.
    """
    return _extract_dies_with_grid(image, grid, geometry)


def extract_dies_custom(
    image: np.ndarray,
    grid_size: int,
    geometry: WaferGeometry | None = None,
) -> list[dict[str, Any]]:
    """
    Extract dies using a manual square grid (``grid_size`` × ``grid_size``).

    Pitch / offsets are derived internally from wafer geometry.
    """
    rgb = _ensure_analysis_resolution(_to_rgb_array(image))
    geometry = geometry or estimate_wafer_geometry(rgb)
    grid = _manual_grid(geometry, int(grid_size))
    return _extract_dies_with_grid(rgb, grid, geometry)


def _extract_dies_with_grid(
    image: np.ndarray,
    grid: GridInfo,
    geometry: WaferGeometry | None = None,
) -> list[dict[str, Any]]:
    """Shared die extraction implementation."""
    rgb = _ensure_analysis_resolution(_to_rgb_array(image))
    geometry = geometry or estimate_wafer_geometry(rgb)
    mask = create_wafer_mask(
        size=int(rgb.shape[0]),
        center_x=float(geometry.center_x),
        center_y=float(geometry.center_y),
        radius=float(geometry.radius),
    )
    masked = _preprocess_apply_wafer_mask(rgb, mask)
    gray = _to_gray(masked if isinstance(masked, np.ndarray) else rgb)
    threshold = _defect_threshold(gray, mask)

    pitch = float(grid.pitch)
    half = pitch / 2.0
    height, width = gray.shape
    dies: list[dict[str, Any]] = []
    die_id = 1

    for row in range(int(grid.rows)):
        for column in range(int(grid.columns)):
            cx = float(grid.offset_x) + column * pitch
            cy = float(grid.offset_y) + row * pitch
            if not _die_center_inside(cx, cy, geometry, margin=half * 0.25):
                continue

            x0 = int(max(0, np.floor(cx - half)))
            y0 = int(max(0, np.floor(cy - half)))
            x1 = int(min(width, np.ceil(cx + half)))
            y1 = int(min(height, np.ceil(cy + half)))
            if x1 <= x0 or y1 <= y0:
                continue

            status = _classify_die_status(
                gray,
                mask,
                (x0, y0, x1, y1),
                threshold,
                rgb=rgb,
                center=(cx, cy),
            )
            dies.append(
                {
                    "die_id": die_id,
                    "row": int(row),
                    "column": int(column),
                    "x": int(round(cx)),
                    "y": int(round(cy)),
                    "bbox": {
                        "x0": x0,
                        "y0": y0,
                        "x1": x1,
                        "y1": y1,
                    },
                    "status": status,
                }
            )
            die_id += 1

    if not dies:
        raise DieAnalysisError(
            "Die extraction produced zero dies. Check grid settings / wafer mask."
        )
    return dies


# ---------------------------------------------------------------------------
# Yield
# ---------------------------------------------------------------------------


def calculate_yield(dies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """
    Compute yield statistics from extracted dies.

    Yield % = (Good Dies / Total Dies) × 100
    """
    if not dies:
        raise DieAnalysisError("Cannot calculate yield from an empty die list.")

    total = len(dies)
    good = sum(1 for die in dies if str(die.get("status", "")).upper() == "GOOD")
    fail = sum(1 for die in dies if str(die.get("status", "")).upper() == "FAIL")
    if good + fail != total:
        # Treat unknown statuses as FAIL for conservative manufacturing analytics
        fail = total - good
    yield_percent = (float(good) / float(total)) * 100.0 if total else 0.0
    return {
        "good_dies": int(good),
        "fail_dies": int(fail),
        "total_dies": int(total),
        "yield_percent": round(yield_percent, 4),
    }


# ---------------------------------------------------------------------------
# Full wafer analysis
# ---------------------------------------------------------------------------


def analyze_wafer(
    image: str | Path | Image.Image | np.ndarray,
    prediction: Mapping[str, Any],
    *,
    mode: str = "automatic",
    grid_size: int | None = None,
    wafer_id: str | None = None,
) -> dict[str, Any]:
    """
    Run the full die extraction / yield pipeline.

    Args:
        image: Wafer RGB image (path / PIL / NumPy). Analysis uses 224×224.
        prediction: Result from ``predict.py`` (must include defect type + confidence).
            This function never re-runs CNN inference.
        mode: ``automatic`` (default) or ``manual``.
        grid_size: Required for manual mode (rows = columns = grid_size).
        wafer_id: Optional identifier for reports / dashboards.

    Returns:
        Structured JSON with classification, yield, grid, geometry, and dies.
    """
    rgb = _ensure_analysis_resolution(_to_rgb_array(image))
    masked = apply_wafer_mask(rgb)
    geometry = estimate_wafer_geometry(masked)

    normalized_mode = mode.strip().lower()
    if normalized_mode in {"manual", "custom"}:
        if grid_size is None:
            raise GridDetectionError("Manual mode requires grid_size.")
        grid = detect_grid(masked, geometry, mode="manual", grid_size=grid_size)
        dies = extract_dies_custom(masked, int(grid_size), geometry)
        # Keep grid info consistent with extraction
        grid = _manual_grid(geometry, int(grid_size))
    else:
        # Automatic mode: lattice + clipping share canonical mask geometry so
        # same-layout wafers keep identical die coordinates / counts.
        scale = float(masked.shape[0]) / float(IMG_SIZE)
        lattice_geometry = WaferGeometry(
            center_x=CENTER_X * scale,
            center_y=CENTER_Y * scale,
            radius=WAFER_RADIUS * scale,
        )
        grid = detect_grid(masked, lattice_geometry, mode="automatic")
        dies = extract_dies(masked, grid, lattice_geometry)
        geometry = lattice_geometry

    yield_summary = calculate_yield(dies)
    classification = _normalize_prediction(prediction)

    resolved_id = wafer_id
    if resolved_id is None and isinstance(image, (str, Path)):
        resolved_id = Path(image).stem
    if resolved_id is None:
        resolved_id = "wafer"

    result = {
        "wafer_id": resolved_id,
        "classification": classification,
        "yield_summary": yield_summary,
        "grid_info": grid.to_dict(),
        "wafer_geometry": {
            "center_x": round(geometry.center_x, 4),
            "center_y": round(geometry.center_y, 4),
            "radius": round(geometry.radius, 4),
        },
        "wafer_summary": {
            "wafer_id": resolved_id,
            "defect_type": classification["defect_type"],
            "confidence": classification["confidence"],
            "grid_mode": grid.mode,
            "rows": grid.rows,
            "columns": grid.columns,
            "pitch": round(float(grid.pitch), 4),
            "offset_x": round(float(grid.offset_x), 4),
            "offset_y": round(float(grid.offset_y), 4),
            "center_x": round(geometry.center_x, 4),
            "center_y": round(geometry.center_y, 4),
            "radius": round(geometry.radius, 4),
            "good_dies": yield_summary["good_dies"],
            "fail_dies": yield_summary["fail_dies"],
            "total_dies": yield_summary["total_dies"],
            "yield_percent": yield_summary["yield_percent"],
        },
        "dies": dies,
    }
    logger.info(
        "Wafer %s analyzed: mode=%s dies=%d yield=%.2f%%",
        resolved_id,
        grid.mode,
        yield_summary["total_dies"],
        yield_summary["yield_percent"],
    )
    return result


def _normalize_prediction(prediction: Mapping[str, Any]) -> dict[str, Any]:
    """Extract defect_type / confidence from a predict.py result mapping."""
    if not isinstance(prediction, Mapping):
        raise DieAnalysisError("prediction must be a mapping from predict.py.")

    defect_type = prediction.get("defect_type")
    confidence = prediction.get("confidence")

    # Allow nested {"prediction": {...}} payloads from Grad-CAM style results
    if defect_type is None and isinstance(prediction.get("prediction"), Mapping):
        nested = prediction["prediction"]
        defect_type = nested.get("class", nested.get("defect_type"))
        confidence = nested.get("confidence", confidence)

    if defect_type is None:
        raise DieAnalysisError(
            "prediction is missing defect_type/class. "
            "Pass the JSON result from predict.py without re-inferring."
        )
    if confidence is None:
        raise DieAnalysisError("prediction is missing confidence.")

    return {
        "defect_type": str(defect_type),
        "confidence": float(confidence),
        "class_index": prediction.get("class_index"),
    }


def analyze_wafers(
    images: Sequence[str | Path | Image.Image | np.ndarray],
    predictions: Sequence[Mapping[str, Any]],
    *,
    mode: str = "automatic",
    grid_size: int | None = None,
) -> list[dict[str, Any]]:
    """Analyze multiple wafers (paired images + predict.py results)."""
    if len(images) != len(predictions):
        raise DieAnalysisError(
            f"images ({len(images)}) and predictions ({len(predictions)}) length mismatch."
        )
    return [
        analyze_wafer(image, prediction, mode=mode, grid_size=grid_size)
        for image, prediction in zip(images, predictions, strict=True)
    ]


__all__ = [
    "DieAnalysisError",
    "InvalidWaferImageError",
    "GridDetectionError",
    "WaferGeometry",
    "GridInfo",
    "FAIL_PIXEL_RATIO",
    "estimate_wafer_geometry",
    "apply_wafer_mask",
    "detect_grid",
    "extract_dies",
    "extract_dies_custom",
    "calculate_yield",
    "analyze_wafer",
    "analyze_wafers",
]
