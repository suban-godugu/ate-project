"""
Failure density / heatmap visualization for WaferVision-AI.

Responsibility: density maps and heatmap overlays ONLY.
Never performs prediction, die extraction, yield, clusters, or zones.
Consumes fail-die coordinates from analysis JSON produced by the pipeline.
"""

from __future__ import annotations

import logging
from typing import Any, Mapping, Sequence

import cv2
import numpy as np

from .wafer_constants import IMG_SIZE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Visualization configuration (density / heatmap)
# ---------------------------------------------------------------------------
DEFAULT_DENSITY_SIZE: int = IMG_SIZE
DEFAULT_GAUSSIAN_SIGMA_SCALE: float = 1.25
DEFAULT_MIN_SIGMA: float = 2.0
DEFAULT_HEATMAP_ALPHA: float = 0.45
# Normalized density at or below this stays black (kills isolated speckle).
DEFAULT_DENSITY_FLOOR: float = 0.42
# Edge length of the delivered density PNG; the KDE field itself stays at
# IMG_SIZE and is upsampled before colorization to avoid color bleeding.
DEFAULT_DENSITY_RENDER_SIZE: int = 1024


class DensityMapError(Exception):
    """Base exception for density / heatmap failures."""


def apply_gaussian_smoothing(
    density: np.ndarray,
    *,
    sigma: float | None = None,
    pitch: float | None = None,
) -> np.ndarray:
    """
    Apply Gaussian smoothing to a raw density field.

    If ``sigma`` is omitted, it is derived from ``pitch`` (or a default).
    """
    if density.ndim != 2:
        raise DensityMapError(f"Density must be 2-D; got shape={density.shape}.")
    field = density.astype(np.float32, copy=True)

    if sigma is None:
        base_pitch = float(pitch) if pitch is not None else 4.0
        sigma = max(base_pitch * DEFAULT_GAUSSIAN_SIGMA_SCALE, DEFAULT_MIN_SIGMA)
    sigma = float(sigma)
    if sigma <= 0:
        raise DensityMapError(f"sigma must be > 0; got {sigma}.")

    ksize = int(max(3, round(sigma * 6)))
    if ksize % 2 == 0:
        ksize += 1
    return cv2.GaussianBlur(field, (ksize, ksize), sigmaX=sigma, sigmaY=sigma)


def normalize_density(density: np.ndarray) -> np.ndarray:
    """Normalize density values to ``[0, 1]`` with dynamic scaling."""
    if density.ndim != 2:
        raise DensityMapError(f"Density must be 2-D; got shape={density.shape}.")
    field = density.astype(np.float32, copy=True)
    max_value = float(field.max()) if field.size else 0.0
    if max_value <= 0.0:
        return np.zeros_like(field, dtype=np.float32)
    return np.clip(field / max_value, 0.0, 1.0)


def _blue_green_yellow_orange_red(
    normalized: np.ndarray,
    floor: float = DEFAULT_DENSITY_FLOOR,
) -> np.ndarray:
    """
    Map density to RGB: Blue→Green→Yellow→Red hotspots.

    Density at or below ``floor`` stays black so only failure clusters are
    visible (not a solid blue wafer disc or isolated single-die speckle).
    """
    t = np.clip(normalized.astype(np.float32), 0.0, 1.0)
    active = t > float(floor)
    if not np.any(active):
        return np.zeros(t.shape + (3,), dtype=np.uint8)

    # Re-stretch active region to full colormap range.
    t_active = t[active]
    lo = float(t_active.min())
    hi = float(t_active.max())
    span = max(hi - lo, 1e-6)
    t_mapped = np.zeros_like(t)
    t_mapped[active] = (t[active] - lo) / span

    stops = np.array(
        [
            [0.00, 0, 80, 255],     # blue (low cluster)
            [0.35, 0, 200, 0],      # green (medium)
            [0.65, 255, 255, 0],    # yellow (high)
            [1.00, 220, 20, 20],    # red (hotspot)
        ],
        dtype=np.float32,
    )

    rgb = np.zeros(t.shape + (3,), dtype=np.float32)
    for channel in range(3):
        rgb[:, :, channel] = np.interp(t_mapped, stops[:, 0], stops[:, channel + 1])
    rgb[~active] = 0.0
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _wafer_circle_mask(
    size: int,
    geometry: Mapping[str, Any] | None,
    scale: float = 1.0,
) -> np.ndarray:
    """
    Boolean mask for the circular wafer region.

    ``scale`` maps geometry expressed in analysis space onto a larger render
    canvas so upscaled heatmaps stay clipped to the wafer edge.
    """
    if geometry:
        cx = float(geometry.get("center_x", size / (2.0 * scale))) * scale
        cy = float(geometry.get("center_y", size / (2.0 * scale))) * scale
        radius = float(geometry.get("radius", size / (2.0 * scale))) * scale
    else:
        cx = cy = size / 2.0
        radius = size / 2.0
    yy, xx = np.ogrid[:size, :size]
    return ((xx - cx) ** 2 + (yy - cy) ** 2) <= (radius ** 2)


def generate_density_map(
    dies: Sequence[Mapping[str, Any]],
    *,
    geometry: Mapping[str, Any] | None = None,
    grid_info: Mapping[str, Any] | None = None,
    size: int = DEFAULT_DENSITY_SIZE,
    sigma: float | None = None,
    as_rgb: bool = True,
    floor: float = DEFAULT_DENSITY_FLOOR,
    render_size: int | None = None,
) -> np.ndarray:
    """
    Generate a failure density map from FAIL die coordinates.

    Pipeline: FAIL points → Gaussian KDE → normalize → wafer mask → heatmap.

    Args:
        dies: Die records from analysis JSON (``status``, ``x``, ``y``).
        geometry: Optional ``wafer_geometry`` for circular masking.
        grid_info: Optional grid info (uses ``pitch`` for Gaussian scale).
        size: KDE field edge length (analysis space, default ``IMG_SIZE``).
        sigma: Optional Gaussian sigma override.
        as_rgb: If True, return colorized RGB; else normalized float field.
        floor: Normalized density at or below this renders black.
        render_size: Optional larger output edge length. The scalar field is
            upsampled before colorization so hues never bleed across stops.
    """
    if size <= 0:
        raise DensityMapError(f"size must be positive; got {size}.")
    if render_size is not None and render_size < size:
        raise DensityMapError(
            f"render_size must be >= size; got {render_size} < {size}."
        )
    if not dies:
        out = int(render_size or size)
        blank = np.zeros((out, out), dtype=np.float32)
        return _blue_green_yellow_orange_red(blank, floor) if as_rgb else blank

    raw = np.zeros((size, size), dtype=np.float32)
    fail_count = 0
    for die in dies:
        if str(die.get("status", "")).upper() != "FAIL":
            continue
        x = int(die.get("x", -1))
        y = int(die.get("y", -1))
        if 0 <= x < size and 0 <= y < size:
            raw[y, x] += 1.0
            fail_count += 1

    pitch = None
    if grid_info is not None and "pitch" in grid_info:
        pitch = float(grid_info["pitch"])

    smoothed = apply_gaussian_smoothing(raw, sigma=sigma, pitch=pitch)
    normalized = normalize_density(smoothed)
    mask = _wafer_circle_mask(size, geometry)
    normalized = normalized * mask.astype(np.float32)

    out_size = int(render_size or size)
    if out_size != size:
        normalized = np.clip(
            cv2.resize(normalized, (out_size, out_size), interpolation=cv2.INTER_CUBIC),
            0.0,
            1.0,
        )
        mask = _wafer_circle_mask(out_size, geometry, scale=out_size / float(size))
        normalized = normalized * mask.astype(np.float32)

    logger.debug(
        "Density map built from %d FAIL dies (field=%d, render=%d)",
        fail_count,
        size,
        out_size,
    )
    if not as_rgb:
        return normalized

    colored = _blue_green_yellow_orange_red(normalized, floor)
    colored[~mask] = 0
    return colored


def overlay_heatmap(
    original_rgb: np.ndarray,
    density_rgb_or_field: np.ndarray,
    *,
    alpha: float = DEFAULT_HEATMAP_ALPHA,
    geometry: Mapping[str, Any] | None = None,
) -> np.ndarray:
    """
    Overlay a density heatmap onto the original wafer image.

    ``density_rgb_or_field`` may be RGB uint8 or a float field in ``[0, 1]``.
    """
    if not 0.0 <= float(alpha) <= 1.0:
        raise DensityMapError(f"alpha must be in [0, 1]; got {alpha}.")
    if original_rgb.ndim != 3 or original_rgb.shape[2] != 3:
        raise DensityMapError(
            f"original_rgb must be HxWx3; got shape={original_rgb.shape}."
        )

    original = original_rgb
    if original.dtype != np.uint8:
        original = np.clip(original, 0, 255).astype(np.uint8)

    if density_rgb_or_field.ndim == 2:
        heat = _blue_green_yellow_orange_red(normalize_density(density_rgb_or_field))
    elif density_rgb_or_field.ndim == 3 and density_rgb_or_field.shape[2] == 3:
        heat = density_rgb_or_field
        if heat.dtype != np.uint8:
            heat = np.clip(heat, 0, 255).astype(np.uint8)
    else:
        raise DensityMapError(
            f"Unsupported density shape: {density_rgb_or_field.shape}."
        )

    if heat.shape[:2] != original.shape[:2]:
        heat = cv2.resize(
            heat,
            (original.shape[1], original.shape[0]),
            interpolation=cv2.INTER_LINEAR,
        )

    blended = (
        (1.0 - float(alpha)) * original.astype(np.float32)
        + float(alpha) * heat.astype(np.float32)
    )
    result = np.clip(blended, 0, 255).astype(np.uint8)

    mask = _wafer_circle_mask(int(result.shape[0]), geometry)
    result[~mask] = original[~mask]
    return result


def generate_density_from_analysis(
    analysis: Mapping[str, Any],
    *,
    size: int = DEFAULT_DENSITY_SIZE,
    sigma: float | None = None,
    as_rgb: bool = True,
) -> np.ndarray:
    """Build a density map directly from ``run_wafer_analysis()`` JSON."""
    dies = analysis.get("dies")
    if dies is None:
        raise DensityMapError("Analysis JSON is missing 'dies'.")
    return generate_density_map(
        dies,
        geometry=analysis.get("wafer_geometry"),
        grid_info=analysis.get("grid_info"),
        size=size,
        sigma=sigma,
        as_rgb=as_rgb,
    )


__all__ = [
    "DensityMapError",
    "DEFAULT_DENSITY_FLOOR",
    "DEFAULT_DENSITY_RENDER_SIZE",
    "DEFAULT_DENSITY_SIZE",
    "DEFAULT_HEATMAP_ALPHA",
    "apply_gaussian_smoothing",
    "normalize_density",
    "generate_density_map",
    "overlay_heatmap",
    "generate_density_from_analysis",
]
