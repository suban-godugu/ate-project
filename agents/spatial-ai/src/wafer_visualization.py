"""
Wafer visualization engine for WaferVision-AI.

Responsibility: render professional semiconductor overlays and report images.
Never performs prediction, die extraction, yield, clusters, or zones.

Consumes analysis JSON from ``run_wafer_analysis()`` plus optional original /
Grad-CAM image arrays (or base64 payloads already present in the JSON).
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2
import numpy as np
from PIL import Image

from .config import PROJECT_ROOT
from .gradcam import encode_base64
from .overlay_heatmap import (
    DEFAULT_HEATMAP_ALPHA,
    DensityMapError,
    generate_density_from_analysis,
    overlay_heatmap,
)
from .wafer_constants import IMG_SIZE

logger = logging.getLogger(__name__)

VISUALIZATIONS_DIR: Path = PROJECT_ROOT / "visualizations"

# ---------------------------------------------------------------------------
# Visualization configuration
# ---------------------------------------------------------------------------
DEFAULT_OVERLAY_ALPHA: float = 0.45
DEFAULT_GRID_COLOR: tuple[int, int, int] = (180, 180, 180)
DEFAULT_GRID_THICKNESS: int = 1
DEFAULT_BOUNDARY_COLOR: tuple[int, int, int] = (255, 255, 255)
DEFAULT_BOUNDARY_THICKNESS: int = 2
DEFAULT_CENTER_COLOR: tuple[int, int, int] = (255, 255, 0)
DEFAULT_GOOD_COLOR: tuple[int, int, int] = (40, 200, 80)
DEFAULT_FAIL_COLOR: tuple[int, int, int] = (220, 40, 40)
DEFAULT_DIE_RADIUS: int = 2
DEFAULT_DIE_RADIUS_FROM_PITCH_SCALE: float = 0.28


class VisualizationError(Exception):
    """Base exception for visualization failures."""


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------


def _ensure_uint8_rgb(image: np.ndarray) -> np.ndarray:
    """Validate / convert to contiguous uint8 RGB."""
    if not isinstance(image, np.ndarray):
        raise VisualizationError(f"Expected numpy image; got {type(image)!r}.")
    if image.ndim != 3 or image.shape[2] != 3:
        raise VisualizationError(f"Expected HxWx3 RGB; got shape={image.shape}.")
    if image.dtype != np.uint8:
        image = np.clip(image, 0, 255).astype(np.uint8)
    return np.ascontiguousarray(image)


def _decode_base64_image(payload: str) -> np.ndarray:
    """Decode a base64 PNG/JPEG string to RGB uint8."""
    try:
        raw = base64.b64decode(payload)
        array = np.frombuffer(raw, dtype=np.uint8)
        bgr = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if bgr is None:
            raise VisualizationError("cv2.imdecode returned None for base64 payload.")
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    except Exception as exc:  # noqa: BLE001
        raise VisualizationError(f"Failed to decode base64 image: {exc}") from exc


def _resolve_original_image(
    analysis: Mapping[str, Any],
    original: np.ndarray | Image.Image | str | Path | None,
) -> np.ndarray:
    """Resolve the original RGB image from argument or analysis JSON."""
    if original is not None:
        if isinstance(original, Image.Image):
            return np.asarray(original.convert("RGB"), dtype=np.uint8)
        if isinstance(original, (str, Path)) and Path(original).is_file():
            with Image.open(original) as handle:
                return np.asarray(handle.convert("RGB"), dtype=np.uint8)
        if isinstance(original, np.ndarray):
            return _ensure_uint8_rgb(original)
        if isinstance(original, str):
            # treat as base64
            return _decode_base64_image(original)

    images = analysis.get("images") or {}
    if isinstance(images, Mapping) and images.get("original"):
        return _decode_base64_image(str(images["original"]))

    raise VisualizationError(
        "Missing original image. Pass original RGB or include "
        "analysis['images']['original'] base64 from run_wafer_analysis()."
    )


def _resize_square(image: np.ndarray, size: int = IMG_SIZE) -> np.ndarray:
    """Resize to square analysis resolution."""
    rgb = _ensure_uint8_rgb(image)
    if rgb.shape[0] == size and rgb.shape[1] == size:
        return rgb
    return cv2.resize(rgb, (size, size), interpolation=cv2.INTER_AREA)


def to_pil(image: np.ndarray) -> Image.Image:
    """Convert RGB numpy array to PIL Image."""
    return Image.fromarray(_ensure_uint8_rgb(image), mode="RGB")


def to_cv2_bgr(image: np.ndarray) -> np.ndarray:
    """Convert RGB numpy array to OpenCV BGR."""
    return cv2.cvtColor(_ensure_uint8_rgb(image), cv2.COLOR_RGB2BGR)


# ---------------------------------------------------------------------------
# Drawing primitives
# ---------------------------------------------------------------------------


def draw_wafer_boundary(
    canvas: np.ndarray,
    geometry: Mapping[str, Any],
    *,
    color: tuple[int, int, int] = DEFAULT_BOUNDARY_COLOR,
    thickness: int = DEFAULT_BOUNDARY_THICKNESS,
    draw_center: bool = True,
) -> np.ndarray:
    """Draw the circular wafer boundary and optional center point."""
    if not geometry:
        raise VisualizationError("Missing wafer geometry for boundary drawing.")
    output = _ensure_uint8_rgb(canvas).copy()
    cx = int(round(float(geometry["center_x"])))
    cy = int(round(float(geometry["center_y"])))
    radius = int(round(float(geometry["radius"])))
    cv2.circle(output, (cx, cy), max(radius - 1, 1), color, int(thickness), cv2.LINE_AA)
    if draw_center:
        cv2.circle(output, (cx, cy), 2, DEFAULT_CENTER_COLOR, -1, cv2.LINE_AA)
    return output


def draw_grid(
    canvas: np.ndarray,
    grid_info: Mapping[str, Any],
    geometry: Mapping[str, Any],
    *,
    color: tuple[int, int, int] = DEFAULT_GRID_COLOR,
    thickness: int = DEFAULT_GRID_THICKNESS,
) -> np.ndarray:
    """Draw horizontal / vertical grid lines clipped to the wafer circle."""
    if not grid_info:
        raise VisualizationError("Missing grid_info for grid drawing.")
    if not geometry:
        raise VisualizationError("Missing wafer_geometry for grid drawing.")

    output = _ensure_uint8_rgb(canvas).copy()
    pitch = float(grid_info.get("pitch", 0))
    if pitch <= 0:
        raise VisualizationError(f"Invalid grid pitch: {pitch}.")

    rows = int(grid_info.get("rows", 0))
    cols = int(grid_info.get("columns", 0))
    offset_x = float(grid_info.get("offset_x", 0.0))
    offset_y = float(grid_info.get("offset_y", 0.0))
    cx = float(geometry["center_x"])
    cy = float(geometry["center_y"])
    radius = float(geometry["radius"])

    height, width = output.shape[:2]

    # Vertical lines through column centers ± half pitch edges
    for column in range(cols + 1):
        x = int(round(offset_x - pitch / 2.0 + column * pitch))
        if 0 <= x < width:
            _draw_line_inside_circle(
                output, (x, 0), (x, height - 1), cx, cy, radius, color, thickness
            )

    for row in range(rows + 1):
        y = int(round(offset_y - pitch / 2.0 + row * pitch))
        if 0 <= y < height:
            _draw_line_inside_circle(
                output, (0, y), (width - 1, y), cx, cy, radius, color, thickness
            )
    return output


def _draw_line_inside_circle(
    canvas: np.ndarray,
    p1: tuple[int, int],
    p2: tuple[int, int],
    cx: float,
    cy: float,
    radius: float,
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    """Draw a line segment clipped approximately to the wafer circle."""
    # Sample points along the line and draw short segments inside the circle
    x0, y0 = p1
    x1, y1 = p2
    steps = max(abs(x1 - x0), abs(y1 - y0), 1)
    prev: tuple[int, int] | None = None
    for step in range(steps + 1):
        t = step / steps
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        inside = (x - cx) ** 2 + (y - cy) ** 2 <= radius ** 2
        if inside:
            if prev is not None:
                cv2.line(canvas, prev, (x, y), color, thickness, cv2.LINE_AA)
            prev = (x, y)
        else:
            prev = None


def draw_die_status(
    canvas: np.ndarray,
    dies: Sequence[Mapping[str, Any]],
    grid_info: Mapping[str, Any] | None = None,
    *,
    good_color: tuple[int, int, int] = DEFAULT_GOOD_COLOR,
    fail_color: tuple[int, int, int] = DEFAULT_FAIL_COLOR,
    radius: int | None = None,
    fail_only: bool = True,
    draw_good_outline: bool = False,
) -> np.ndarray:
    """
    Draw die markers.

    Default: FAIL-only filled markers. Optionally outline GOOD dies.
    Caller should alpha-blend this layer over the original wafer.
    """
    if dies is None:
        raise VisualizationError("Die list is missing.")
    output = _ensure_uint8_rgb(canvas).copy()

    if radius is None:
        pitch = float((grid_info or {}).get("pitch", 4.0))
        radius = max(
            DEFAULT_DIE_RADIUS,
            int(round(pitch * DEFAULT_DIE_RADIUS_FROM_PITCH_SCALE)),
        )

    if len(dies) == 0:
        return output

    for die in dies:
        x = int(die.get("x", -1))
        y = int(die.get("y", -1))
        if x < 0 or y < 0:
            continue
        status = str(die.get("status", "")).upper()
        if status == "FAIL":
            cv2.circle(output, (x, y), int(radius), fail_color, -1, cv2.LINE_AA)
        elif (not fail_only or draw_good_outline) and status in {"GOOD", "PASS"}:
            cv2.circle(output, (x, y), int(radius), good_color, 1, cv2.LINE_AA)
    return output


def draw_overlay(
    original: np.ndarray,
    analysis: Mapping[str, Any],
    *,
    alpha: float = 0.38,
    draw_grid_lines: bool = False,
    grid_color: tuple[int, int, int] = DEFAULT_GRID_COLOR,
    grid_thickness: int = DEFAULT_GRID_THICKNESS,
    boundary_thickness: int = 0,
    die_radius: int | None = None,
    fail_only: bool = True,
    draw_good_outline: bool = False,
    draw_fail_border: bool = True,
) -> np.ndarray:
    """
    Failure overlay for commercial-style yield analysis:

    - Keep the original wafer fully visible underneath
    - Semi-transparent red fill on FAIL dies only
    - Optional thin red border around each failed die
    """
    if not 0.0 <= float(alpha) <= 1.0:
        raise VisualizationError(f"alpha must be in [0, 1]; got {alpha}.")

    base = _resize_square(_ensure_uint8_rgb(original))
    geometry = analysis.get("wafer_geometry")
    grid_info = analysis.get("grid_info")
    dies = analysis.get("dies")
    if geometry is None:
        raise VisualizationError("Analysis JSON missing wafer_geometry.")
    if dies is None:
        raise VisualizationError("Analysis JSON missing dies.")

    output = base.copy()
    if draw_grid_lines and grid_info is not None:
        output = draw_grid(
            output,
            grid_info,
            geometry,
            color=grid_color,
            thickness=grid_thickness,
        )

    pitch = float((grid_info or {}).get("pitch", 4.0))
    # Keep markers smaller than the die so cyan/yellow bin color stays readable.
    half = max(int(round(pitch * 0.28)), 1)
    if die_radius is None:
        die_radius = half
    border_half = max(int(round(pitch * 0.40)), half + 1)

    marker = np.zeros_like(base)
    marker_mask = np.zeros(base.shape[:2], dtype=np.float32)
    border_rects: list[tuple[int, int, int, int]] = []

    for die in dies:
        status = str(die.get("status", "")).upper()
        x = int(die.get("x", -1))
        y = int(die.get("y", -1))
        if x < 0 or y < 0:
            continue

        if status != "FAIL":
            if draw_good_outline and status in {"GOOD", "PASS"}:
                cv2.circle(output, (x, y), int(die_radius), DEFAULT_GOOD_COLOR, 1, cv2.LINE_AA)
            continue

        x0 = max(0, x - half)
        y0 = max(0, y - half)
        x1 = min(base.shape[1], x + half + 1)
        y1 = min(base.shape[0], y + half + 1)
        if x1 <= x0 or y1 <= y0:
            continue

        # Soft red wash — original yellow/orange die remains visible underneath.
        marker[y0:y1, x0:x1] = DEFAULT_FAIL_COLOR
        marker_mask[y0:y1, x0:x1] = float(alpha)

        bx0 = max(0, x - border_half)
        by0 = max(0, y - border_half)
        bx1 = min(base.shape[1] - 1, x + border_half)
        by1 = min(base.shape[0] - 1, y + border_half)
        border_rects.append((bx0, by0, bx1, by1))

    a = marker_mask[..., None]
    output = np.clip(
        (1.0 - a) * output.astype(np.float32) + a * marker.astype(np.float32),
        0,
        255,
    ).astype(np.uint8)

    if draw_fail_border:
        for x0, y0, x1, y1 in border_rects:
            cv2.rectangle(output, (x0, y0), (x1, y1), DEFAULT_FAIL_COLOR, 1, cv2.LINE_AA)

    if int(boundary_thickness) > 0:
        output = draw_wafer_boundary(
            output,
            geometry,
            thickness=boundary_thickness,
        )
    return output


def generate_combined_view(
    original: np.ndarray,
    overlay: np.ndarray,
    density: np.ndarray,
    gradcam: np.ndarray,
    *,
    labels: tuple[str, str, str, str] = (
        "Original",
        "Overlay",
        "Density",
        "Grad-CAM",
    ),
) -> np.ndarray:
    """
    Create a 2×2 report image: Original | Overlay / Density | Grad-CAM.
    """
    tiles = [
        _resize_square(_ensure_uint8_rgb(original)),
        _resize_square(_ensure_uint8_rgb(overlay)),
        _resize_square(_ensure_uint8_rgb(density)),
        _resize_square(_ensure_uint8_rgb(gradcam)),
    ]
    labeled: list[np.ndarray] = []
    for tile, label in zip(tiles, labels, strict=True):
        labeled.append(_label_tile(tile, label))

    top = np.concatenate(labeled[0:2], axis=1)
    bottom = np.concatenate(labeled[2:4], axis=1)
    return np.concatenate([top, bottom], axis=0)


def _label_tile(image: np.ndarray, text: str) -> np.ndarray:
    """Add a small title bar above a tile."""
    bar_height = 22
    width = image.shape[1]
    bar = np.zeros((bar_height, width, 3), dtype=np.uint8)
    cv2.putText(
        bar,
        text,
        (8, 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (230, 230, 230),
        1,
        cv2.LINE_AA,
    )
    return np.concatenate([bar, image], axis=0)


# ---------------------------------------------------------------------------
# Grad-CAM reuse (no recomputation)
# ---------------------------------------------------------------------------


def _resolve_gradcam_images(
    analysis: Mapping[str, Any],
    *,
    gradcam_heatmap: np.ndarray | None = None,
    gradcam_overlay: np.ndarray | None = None,
) -> tuple[np.ndarray | None, np.ndarray | None]:
    """Resolve Grad-CAM images from args or analysis base64 payloads."""
    images = analysis.get("images") or {}
    heatmap = gradcam_heatmap
    overlay = gradcam_overlay

    if heatmap is None and isinstance(images, Mapping) and images.get("heatmap"):
        heatmap = _decode_base64_image(str(images["heatmap"]))
    if overlay is None and isinstance(images, Mapping) and images.get("gradcam"):
        overlay = _decode_base64_image(str(images["gradcam"]))

    return (
        None if heatmap is None else _resize_square(_ensure_uint8_rgb(heatmap)),
        None if overlay is None else _resize_square(_ensure_uint8_rgb(overlay)),
    )


# ---------------------------------------------------------------------------
# Full visualization suite
# ---------------------------------------------------------------------------


def generate_visualizations(
    analysis: Mapping[str, Any],
    *,
    original: np.ndarray | Image.Image | str | Path | None = None,
    gradcam_heatmap: np.ndarray | None = None,
    gradcam_overlay: np.ndarray | None = None,
    overlay_alpha: float = DEFAULT_OVERLAY_ALPHA,
    heatmap_alpha: float = DEFAULT_HEATMAP_ALPHA,
    save: bool = True,
    output_dir: Path | str | None = None,
    include_base64: bool = True,
) -> dict[str, Any]:
    """
    Build the full visualization suite from ``run_wafer_analysis()`` JSON.

    Does not re-run prediction, Grad-CAM, or die analysis.
    """
    if not isinstance(analysis, Mapping):
        raise VisualizationError("analysis must be a mapping from run_wafer_analysis().")

    try:
        original_rgb = _resize_square(_resolve_original_image(analysis, original))
        overlay = draw_overlay(original_rgb, analysis, alpha=overlay_alpha)
        density = generate_density_from_analysis(analysis, size=original_rgb.shape[0])
        density_on_wafer = overlay_heatmap(
            original_rgb,
            density,
            alpha=heatmap_alpha,
            geometry=analysis.get("wafer_geometry"),
        )

        heat, gcam = _resolve_gradcam_images(
            analysis,
            gradcam_heatmap=gradcam_heatmap,
            gradcam_overlay=gradcam_overlay,
        )
        if heat is None:
            heat = density.copy()
        if gcam is None:
            gcam = overlay.copy()

        combined = generate_combined_view(original_rgb, overlay, density, gcam)
    except (DensityMapError, VisualizationError):
        raise
    except Exception as exc:  # noqa: BLE001
        raise VisualizationError(f"Visualization generation failed: {exc}") from exc

    arrays = {
        "original": original_rgb,
        "overlay": overlay,
        "density": density,
        "density_overlay": density_on_wafer,
        "gradcam": gcam,
        "heatmap": heat,
        "combined": combined,
    }
    pil_images = {key: to_pil(value) for key, value in arrays.items()}

    result: dict[str, Any] = {
        "arrays": arrays,
        "pil": pil_images,
        "cv2_bgr": {key: to_cv2_bgr(value) for key, value in arrays.items()},
    }
    if include_base64:
        try:
            result["base64"] = {
                key: encode_base64(value) for key, value in arrays.items()
            }
        except Exception as exc:  # noqa: BLE001
            raise VisualizationError(f"Base64 encoding failed: {exc}") from exc

    saved: dict[str, str] = {}
    if save:
        saved = save_visualizations(arrays, output_dir=output_dir)
        result["saved_files"] = saved

    _print_visualization_summary(saved or {k: "(not saved)" for k in arrays}, output_dir)
    return result


def save_visualizations(
    images: Mapping[str, np.ndarray],
    *,
    output_dir: Path | str | None = None,
) -> dict[str, str]:
    """Save standard visualization PNGs under ``visualizations/``."""
    destination = Path(output_dir) if output_dir is not None else VISUALIZATIONS_DIR
    destination.mkdir(parents=True, exist_ok=True)

    mapping = {
        "original": "original.png",
        "overlay": "overlay.png",
        "density": "density.png",
        "gradcam": "gradcam.png",
        "combined": "combined.png",
    }
    saved: dict[str, str] = {}
    for key, filename in mapping.items():
        if key not in images:
            continue
        path = destination / filename
        to_pil(images[key]).save(path)
        saved[key] = str(path.resolve())
    return saved


def _print_visualization_summary(
    saved_files: Mapping[str, str],
    output_dir: Path | str | None,
) -> None:
    """Print the visualization terminal summary."""
    print("=" * 50)
    print("VISUALIZATION GENERATED")
    print("=" * 50)
    print(f"Overlay           : {'yes' if 'overlay' in saved_files else 'n/a'}")
    print(f"Density Map       : {'yes' if 'density' in saved_files else 'n/a'}")
    print(f"GradCAM           : {'yes' if 'gradcam' in saved_files else 'n/a'}")
    print(f"Combined Image    : {'yes' if 'combined' in saved_files else 'n/a'}")
    print(f"Output Directory  : {output_dir or VISUALIZATIONS_DIR}")
    print("=" * 50)


def main(argv: Sequence[str] | None = None) -> int:
    """
    CLI helper::

        python -m src.wafer_visualization <image_path>

    Runs the master pipeline (read-only consumption) then renders visualizations.
    """
    import sys

    from .wafer_pipeline import run_wafer_analysis_from_path

    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m src.wafer_visualization <image_path>")
        return 1

    analysis = run_wafer_analysis_from_path(args[0], include_images=True, save_log=False)
    generate_visualizations(analysis, original=args[0], save=True)
    return 0


__all__ = [
    "VisualizationError",
    "VISUALIZATIONS_DIR",
    "DEFAULT_OVERLAY_ALPHA",
    "draw_wafer_boundary",
    "draw_grid",
    "draw_die_status",
    "draw_overlay",
    "generate_combined_view",
    "generate_visualizations",
    "save_visualizations",
    "to_pil",
    "to_cv2_bgr",
    "encode_base64",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
