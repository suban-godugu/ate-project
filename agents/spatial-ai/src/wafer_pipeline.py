"""
Master wafer analysis pipeline for WaferVision-AI.

Responsibility: single orchestration entry point for end-to-end wafer analysis.

All future consumers (FastAPI, dashboard, batch analysis, reporting) MUST call
``run_wafer_analysis()`` instead of invoking predict / Grad-CAM / die analysis
directly.

Pipeline order (mandatory)::

    Validate → Predict (once) → Grad-CAM → Die/Yield → Overlay → Density
    → Spatial Analytics → JSON

Visualization modules (``wafer_visualization.py`` / ``overlay_heatmap.py``) are
still stubs; die overlay and density rendering are implemented here as pipeline
helpers so the master controller is complete without modifying locked modules.

Spatial analytics (``cluster_analysis`` / ``zone_analysis``) is a pure
post-processing stage appended after die extraction outputs are ready.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import cv2
import numpy as np
from PIL import Image

from .cluster_analysis import ClusterAnalysisError, run_cluster_analysis
from .config import LOGS_DIR, MODEL_PATH
from .dice_analysis import (
    DieAnalysisError,
    GridDetectionError,
    InvalidWaferImageError,
    analyze_wafer,
)
from .gradcam import (
    GradCAM,
    GradCAMError,
    encode_base64 as gradcam_encode_base64,
    generate_overlay as generate_gradcam_overlay,
)
from .predict import (
    PredictionError,
    is_wafer_trained_model,
    load_prediction_model,
    predict_image,
)
from .preprocess import (
    PreprocessError,
    UnsupportedFormatError,
    is_supported_image,
    load_image,
    preprocess_image,
    resize_rgb_to_img_size,
)
from .wafer_constants import IMG_SIZE
from .zone_analysis import ZoneAnalysisError, run_zone_analysis

logger = logging.getLogger(__name__)

# KDE bandwidth as a multiple of die pitch (configurable Gaussian smoothing).
# Kernel width as a multiple of die pitch. Wider kernels merge neighbouring
# clusters into one amorphous blob, so stay close to the die lattice.
DENSITY_BANDWIDTH_SCALE: float = 1.05
# Values below this fraction of the peak fade out instead of being clipped.
DENSITY_FLOOR: float = 0.1


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PipelineError(Exception):
    """Base exception for master pipeline failures."""


class ImageValidationError(PipelineError):
    """Raised when an input wafer image fails validation."""


class ImageEncodingError(PipelineError):
    """Raised when visualization encoding fails."""


# ---------------------------------------------------------------------------
# Image validation / display helpers
# ---------------------------------------------------------------------------


def _validate_input_image(
    image: str | Path | Image.Image | np.ndarray,
) -> None:
    """Validate path / PIL / NumPy inputs before analysis."""
    if isinstance(image, (str, Path)):
        path = Path(image)
        if not path.is_file():
            raise ImageValidationError(f"Wafer image not found: {path}")
        if not is_supported_image(path):
            raise ImageValidationError(
                f"Unsupported image format for {path}. "
                "Supported: jpg, jpeg, png, bmp."
            )
        try:
            load_image(path)
        except UnsupportedFormatError as exc:
            raise ImageValidationError(str(exc)) from exc
        except PreprocessError as exc:
            raise ImageValidationError(f"Invalid / corrupted image: {exc}") from exc
        return

    if isinstance(image, Image.Image):
        if image.size[0] <= 0 or image.size[1] <= 0:
            raise ImageValidationError(f"Empty PIL image size: {image.size}")
        return

    if isinstance(image, np.ndarray):
        if image.size == 0:
            raise ImageValidationError("Empty numpy wafer image.")
        if image.ndim != 3 or image.shape[2] != 3:
            raise ImageValidationError(
                f"Expected RGB array (H, W, 3); got shape={image.shape}."
            )
        return

    raise ImageValidationError(
        f"Unsupported input type: {type(image)!r}. "
        "Expected path, PIL.Image, or numpy.ndarray."
    )


def _display_rgb(image: str | Path | Image.Image | np.ndarray) -> np.ndarray:
    """Return canonical 224×224 uint8 RGB (same lattice as die analysis + Grad-CAM)."""
    try:
        return resize_rgb_to_img_size(image)
    except Exception as exc:  # noqa: BLE001
        raise ImageValidationError(str(exc)) from exc


def _wafer_id_from_input(image: str | Path | Image.Image | np.ndarray) -> str:
    """Derive a stable wafer_id for logs / JSON."""
    if isinstance(image, (str, Path)):
        return Path(image).name
    if isinstance(image, Image.Image):
        return "wafer_pil.png"
    return "wafer_array.png"


# ---------------------------------------------------------------------------
# Grad-CAM (reuse existing prediction — no second classify call)
# ---------------------------------------------------------------------------


def _run_gradcam_with_prediction(
    image: str | Path | Image.Image | np.ndarray,
    prediction: Mapping[str, Any],
    *,
    display_rgb: np.ndarray | None = None,
) -> dict[str, Any]:
    """
    Compute Grad-CAM for the already-predicted class (CNN only).

    ``display_rgb`` must be the same 224×224 canvas used for die overlay/density
    so CAM hotspots align with FAIL markers.
    """
    try:
        engine = GradCAM()
        class_index = int(prediction["class_index"])
        tensor = preprocess_image(image, augment=False).unsqueeze(0)
        # Preserve the native target-layer CAM (normally 7×7 for ResNet50
        # layer4). The frontend interpolates this scalar field directly at
        # device resolution; no PNG resampling is involved.
        native_heatmap = engine._compute_cam(  # noqa: SLF001
            class_index,
            tensor,
            output_size=None,
        )
        original = display_rgb if display_rgb is not None else _display_rgb(image)
        if original.shape[0] != IMG_SIZE or original.shape[1] != IMG_SIZE:
            original = resize_rgb_to_img_size(original)
        # Legacy image artifacts remain available to non-dashboard callers.
        heatmap = native_heatmap
        if native_heatmap.shape[:2] != original.shape[:2]:
            heatmap = cv2.resize(
                np.asarray(native_heatmap, dtype=np.float32),
                (original.shape[1], original.shape[0]),
                interpolation=cv2.INTER_LINEAR,
            )
        heatmap_rgb = cv2.applyColorMap(
            np.uint8(np.clip(heatmap, 0.0, 1.0) * 255.0),
            cv2.COLORMAP_JET,
        )
        heatmap_rgb = cv2.cvtColor(heatmap_rgb, cv2.COLOR_BGR2RGB)
        overlay = generate_gradcam_overlay(original, heatmap, alpha=0.45)
        return {
            "original": original,
            "native_heatmap": native_heatmap,
            "heatmap": heatmap,
            "heatmap_rgb": heatmap_rgb,
            "overlay": overlay,
            "target_layer": engine.target_layer_name,
        }
    except (GradCAMError, PreprocessError, KeyError, TypeError, ValueError) as exc:
        raise PipelineError(f"Grad-CAM failed: {exc}") from exc


def _gradcam_message(
    available: bool,
    wafer_trained: bool,
    error: str | None,
) -> str | None:
    """Explain the Grad-CAM state so the dashboard never shows a bare panel."""
    if not available:
        return error or "Grad-CAM could not be generated for this wafer."
    if not wafer_trained:
        return (
            "Checkpoint head is not wafer-trained (epoch 0), so attention "
            "reflects backbone features rather than learned defect classes."
        )
    return None


def _build_visualization_payload(
    die_result: Mapping[str, Any],
    gradcam: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """
    Build the renderer-neutral visualization contract.

    Coordinates are in the same IMG_SIZE model space as dies and wafer
    geometry. The dashboard scales these values into a device-pixel canvas.
    No overlay, density, or Grad-CAM PNG is required.
    """
    dies = die_result.get("dies") or []
    geometry = die_result.get("wafer_geometry") or {}
    grid = die_result.get("grid_info") or {}
    pitch = float(grid.get("pitch", 4.0))

    failure_points = [
        {
            "x": float(die["x"]),
            "y": float(die["y"]),
            "weight": 1.0,
            "die_id": die.get("die_id"),
        }
        for die in dies
        if str(die.get("status", "")).upper() == "FAIL"
        and die.get("x") is not None
        and die.get("y") is not None
    ]

    gradcam_payload: dict[str, Any] = {
        "available": False,
        "alpha": 0.45,
        "interpolation": "bicubic",
        "heatmap": None,
    }
    if gradcam is not None:
        native = np.asarray(gradcam["native_heatmap"], dtype=np.float32)
        gradcam_payload = {
            "available": True,
            "layer": gradcam.get("target_layer"),
            "alpha": 0.45,
            "interpolation": "bicubic",
            "heatmap": {
                "width": int(native.shape[1]),
                "height": int(native.shape[0]),
                # Flat row-major scalar field keeps JSON smaller than objects.
                "values": np.round(native, 6).ravel().tolist(),
            },
        }

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
            "points": failure_points,
            "sigma": max(pitch * DENSITY_BANDWIDTH_SCALE, 2.5),
            "radius": max(pitch * 3.0, 9.0),
            "floor": DENSITY_FLOOR,
            "normalization": "max",
            "mask": {
                "type": "circle",
                "center_x": float(geometry.get("center_x", IMG_SIZE / 2)),
                "center_y": float(geometry.get("center_y", IMG_SIZE / 2)),
                "radius": float(geometry.get("radius", IMG_SIZE / 2)),
            },
            "color_stops": [
                {"at": 0.00, "color": "#1D4ED8", "label": "Low"},
                {"at": 0.30, "color": "#16A34A", "label": "Medium"},
                {"at": 0.58, "color": "#FACC15", "label": "High"},
                {"at": 0.80, "color": "#F97316", "label": "Very High"},
                {"at": 1.00, "color": "#DC2626", "label": "Critical"},
            ],
        },
        "gradcam": gradcam_payload,
    }


# ---------------------------------------------------------------------------
# Die overlay + failure density (pipeline visualization helpers)
# ---------------------------------------------------------------------------


def _draw_die_overlay(
    original: np.ndarray,
    die_result: Mapping[str, Any],
) -> np.ndarray:
    """
    Overlay on the original wafer (agent visualization module):
      - semi-transparent red markers on FAIL dies only
      - GOOD outlines off by default (optional)
    """
    from .wafer_visualization import draw_overlay

    canvas = original.copy()
    if canvas.dtype != np.uint8:
        canvas = np.clip(canvas, 0, 255).astype(np.uint8)
    if canvas.shape[0] != IMG_SIZE or canvas.shape[1] != IMG_SIZE:
        canvas = resize_rgb_to_img_size(canvas)

    return draw_overlay(
        canvas,
        die_result,
        alpha=0.38,
        draw_grid_lines=False,
        boundary_thickness=0,
        fail_only=True,
        draw_good_outline=False,
        draw_fail_border=True,
    )


def _generate_density_map(
    die_result: Mapping[str, Any],
    *,
    size: int = IMG_SIZE,
    render_size: int | None = None,
    bandwidth: float = DENSITY_BANDWIDTH_SCALE,
    original: np.ndarray | None = None,
) -> np.ndarray:
    """
    Failure-density KDE from FAIL die coordinates only.

    Returns a smooth Blue→Green→Yellow→Red hotspot map on a black background
    masked to the wafer (never a blurred copy of the wafer). ``original`` is
    ignored on purpose so the heatmap is never blended onto the die map.
    """
    from .overlay_heatmap import (
        DEFAULT_DENSITY_RENDER_SIZE,
        generate_density_map as _density_from_dies,
    )

    _ = original  # intentionally unused — density must not blend onto wafer

    if size != IMG_SIZE:
        raise PipelineError(
            f"Density field size must equal IMG_SIZE ({IMG_SIZE}); got {size}."
        )

    dies = die_result.get("dies") or []
    geometry = die_result.get("wafer_geometry") or {}
    grid = die_result.get("grid_info") or {}
    pitch = float(grid.get("pitch", 4.0))
    # Bandwidth tuned so hotspots stay compact without isolated single-die blobs.
    sigma = max(pitch * float(bandwidth), 3.0)

    return _density_from_dies(
        dies,
        geometry=geometry,
        grid_info=grid,
        size=IMG_SIZE,
        sigma=sigma,
        as_rgb=True,
        render_size=int(render_size or DEFAULT_DENSITY_RENDER_SIZE),
    )


# ---------------------------------------------------------------------------
# Encoding / logging
# ---------------------------------------------------------------------------


def encode_images(images: Mapping[str, np.ndarray | Image.Image | None]) -> dict[str, str]:
    """
    Encode visualization arrays as base64 PNG strings for FastAPI / dashboard.
    """
    encoded: dict[str, str] = {}
    try:
        for key, value in images.items():
            if value is None:
                continue
            encoded[key] = gradcam_encode_base64(value)
    except Exception as exc:  # noqa: BLE001
        raise ImageEncodingError(f"Failed to encode pipeline images: {exc}") from exc
    return encoded


def save_wafer_log(
    analysis: Mapping[str, Any],
    *,
    logs_dir: Path | str = LOGS_DIR,
) -> Path:
    """
    Save analysis metadata to ``logs/<wafer_name>.json`` without base64 images.
    """
    destination_dir = Path(logs_dir)
    destination_dir.mkdir(parents=True, exist_ok=True)

    wafer_id = str(analysis.get("wafer_id", "wafer"))
    safe_name = Path(wafer_id).stem or "wafer"
    path = destination_dir / f"{safe_name}.json"

    payload = {
        key: value
        for key, value in analysis.items()
        if key != "images"
    }
    # Drop any accidental nested base64 blobs under alternate keys
    payload.pop("gradcam_arrays", None)

    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    logger.info("Saved wafer log to %s", path)
    return path


# ---------------------------------------------------------------------------
# Master orchestration
# ---------------------------------------------------------------------------


def run_wafer_analysis(
    image: str | Path | Image.Image | np.ndarray,
    *,
    grid_mode: str = "automatic",
    grid_size: int | None = None,
    wafer_id: str | None = None,
    save_log: bool = True,
    include_images: bool = True,
) -> dict[str, Any]:
    """
    Run the full wafer analysis pipeline once.

    Args:
        image: Path, PIL image, or NumPy RGB array.
        grid_mode: ``automatic`` (default) or ``manual``.
        grid_size: Required for manual mode (rows = columns = grid_size).
        wafer_id: Optional override for the wafer identifier.
        save_log: Persist metadata JSON under ``logs/`` (no base64).
        include_images: Include base64 image payloads in the returned dict.

    Returns:
        Dashboard-ready dictionary with classification, yield, grid, geometry,
        dies, and encoded images.
    """
    start = time.perf_counter()
    _validate_input_image(image)
    load_prediction_model()  # singleton — CNN required

    resolved_id = wafer_id or _wafer_id_from_input(image)
    # One shared 224×224 canvas for Original / Overlay / Density / Grad-CAM bases.
    canonical_rgb = _display_rgb(image)

    # Step 2 — Prediction exactly once (CNN)
    try:
        prediction = predict_image(image, verbose=False)
    except PredictionError as exc:
        raise PipelineError(f"Prediction failed: {exc}") from exc

    # Step 3 — Grad-CAM runs whenever a CNN checkpoint is loaded. A frozen or
    # partially trained head still yields a valid attention map; the calibration
    # state travels with the payload instead of blanking the panel.
    wafer_trained = is_wafer_trained_model()
    gradcam: dict[str, Any] | None = None
    gradcam_error: str | None = None
    try:
        gradcam = _run_gradcam_with_prediction(
            image, prediction, display_rgb=canonical_rgb
        )
    except PipelineError as exc:
        gradcam_error = str(exc)
        logger.warning("Grad-CAM unavailable: %s", exc)

    # Step 4 — Die extraction / yield (same resize lattice as canonical_rgb)
    try:
        die_result = analyze_wafer(
            image,
            prediction,
            mode=grid_mode,
            grid_size=grid_size,
            wafer_id=resolved_id,
        )
    except (InvalidWaferImageError, GridDetectionError, DieAnalysisError) as exc:
        raise PipelineError(f"Die analysis failed: {exc}") from exc

    # Step 5 — Renderer-neutral visualization JSON (primary dashboard contract)
    original = canonical_rgb
    visualization = _build_visualization_payload(die_result, gradcam)

    # Compatibility image bundle for legacy/non-dashboard clients only.
    images_b64: dict[str, str] = {}
    if include_images:
        try:
            die_overlay = _draw_die_overlay(original, die_result)
            density = _generate_density_map(die_result, original=None)
        except Exception as exc:  # noqa: BLE001
            raise PipelineError(f"Legacy image generation failed: {exc}") from exc
        image_payload: dict[str, np.ndarray | None] = {
            "original": original,
            "overlay": die_overlay,
            "density": density,
            "gradcam": gradcam["overlay"] if gradcam else None,
            "heatmap": gradcam["heatmap_rgb"] if gradcam else None,
        }
        images_b64 = encode_images(image_payload)

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    result: dict[str, Any] = {
        "wafer_id": resolved_id,
        "classification": die_result.get("classification")
        or {
            "defect_type": prediction.get("defect_type"),
            "confidence": prediction.get("confidence"),
        },
        "yield_summary": die_result["yield_summary"],
        "grid_info": die_result["grid_info"],
        "wafer_geometry": die_result["wafer_geometry"],
        "dies": die_result["dies"],
        "visualization": visualization,
        "wafer_summary": die_result.get("wafer_summary"),
        "gradcam_meta": {
            "available": gradcam is not None,
            "wafer_trained": bool(wafer_trained),
            "layer": (gradcam or {}).get("target_layer"),
            "model": MODEL_PATH.stem,
            "prediction_class": prediction.get("defect_type"),
            "confidence": prediction.get("confidence"),
            "message": _gradcam_message(
                gradcam is not None, bool(wafer_trained), gradcam_error
            ),
        },
        "timing_ms": {
            "total": round(elapsed_ms, 4),
            "prediction": prediction.get("inference_time_ms"),
        },
    }
    if include_images:
        result["images"] = images_b64

    # Spatial analytics — pure post-processing; never mutates earlier fields.
    result["spatial_analysis"] = _compute_spatial_analysis(
        dies=die_result["dies"],
        wafer_geometry=die_result["wafer_geometry"],
        yield_summary=die_result["yield_summary"],
    )

    if save_log:
        result["log_path"] = str(save_wafer_log(result))

    logger.info(
        "Pipeline complete for %s in %.1f ms (yield=%.2f%%)",
        resolved_id,
        elapsed_ms,
        float(result["yield_summary"]["yield_percent"]),
    )
    return result


def _compute_spatial_analysis(
    *,
    dies: Sequence[Mapping[str, Any]],
    wafer_geometry: Mapping[str, Any],
    yield_summary: Mapping[str, Any],
) -> dict[str, Any] | None:
    """
    Run cluster + zone analysis on existing die outputs.

    Returns ``None`` when analytics cannot be computed (schema-stable).
    """
    try:
        t0 = time.perf_counter()
        cluster_payload = run_cluster_analysis(dies, yield_summary)
        cluster_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        zones = run_zone_analysis(dies, wafer_geometry)
        zone_ms = (time.perf_counter() - t1) * 1000.0

        logger.info(
            "Spatial analytics: clusters=%.1f ms zones=%.1f ms",
            cluster_ms,
            zone_ms,
        )
        return {
            "cluster_summary": cluster_payload["cluster_summary"],
            "clusters": cluster_payload["clusters"],
            "zone_analysis": zones,
        }
    except (ClusterAnalysisError, ZoneAnalysisError, KeyError, TypeError, ValueError) as exc:
        logger.warning("Spatial analytics unavailable: %s", exc)
        return None


def run_wafer_analysis_from_path(
    path: str | Path,
    *,
    grid_mode: str = "automatic",
    grid_size: int | None = None,
    save_log: bool = True,
    include_images: bool = True,
) -> dict[str, Any]:
    """Convenience wrapper for filesystem paths."""
    return run_wafer_analysis(
        Path(path),
        grid_mode=grid_mode,
        grid_size=grid_size,
        save_log=save_log,
        include_images=include_images,
    )


def run_batch_analysis(
    images: Sequence[str | Path | Image.Image | np.ndarray],
    *,
    grid_mode: str = "automatic",
    grid_size: int | None = None,
    save_log: bool = True,
    include_images: bool = True,
) -> list[dict[str, Any]]:
    """
    Analyze multiple wafers.

    Reuses the singleton prediction model; the model is never reloaded per wafer.
    """
    if not images:
        raise PipelineError("run_batch_analysis requires at least one image.")

    load_prediction_model()
    results: list[dict[str, Any]] = []
    for index, image in enumerate(images):
        try:
            results.append(
                run_wafer_analysis(
                    image,
                    grid_mode=grid_mode,
                    grid_size=grid_size,
                    save_log=save_log,
                    include_images=include_images,
                )
            )
        except PipelineError as exc:
            raise PipelineError(
                f"Batch analysis failed at index {index}: {exc}"
            ) from exc
    return results


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: ``python -m src.wafer_pipeline <image_path> [--manual N]``."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m src.wafer_pipeline <image_path> [--manual N]")
        return 1

    grid_mode = "automatic"
    grid_size = None
    if "--manual" in args:
        idx = args.index("--manual")
        grid_mode = "manual"
        try:
            grid_size = int(args[idx + 1])
        except (IndexError, ValueError) as exc:
            raise SystemExit("`--manual` requires an integer grid size.") from exc
        del args[idx : idx + 2]

    image_path = args[0]
    result = run_wafer_analysis_from_path(
        image_path,
        grid_mode=grid_mode,
        grid_size=grid_size,
        include_images=True,
    )
    print("=" * 50)
    print("WAFER PIPELINE RESULT")
    print("=" * 50)
    print(f"Wafer ID     : {result['wafer_id']}")
    print(
        f"Prediction   : {result['classification']['defect_type']} "
        f"({result['classification']['confidence']:.2f}%)"
    )
    print(
        f"Yield        : {result['yield_summary']['yield_percent']:.2f}% "
        f"({result['yield_summary']['good_dies']}/"
        f"{result['yield_summary']['total_dies']})"
    )
    print(f"Grid         : {result['grid_info']}")
    print(f"Total time   : {result['timing_ms']['total']:.1f} ms")
    if result.get("log_path"):
        print(f"Log          : {result['log_path']}")
    print("=" * 50)
    return 0


__all__ = [
    "PipelineError",
    "ImageValidationError",
    "ImageEncodingError",
    "run_wafer_analysis",
    "run_wafer_analysis_from_path",
    "run_batch_analysis",
    "save_wafer_log",
    "encode_images",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
