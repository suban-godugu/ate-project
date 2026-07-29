"""
Grad-CAM explainable AI for WaferVision-AI.

Responsibility: explain why the CNN predicted a defect class.

IMPORTANT:
- Never decides the predicted class independently.
- Always obtains prediction from ``predict.py`` (single prediction path).
- Reuses the singleton model from ``predict.load_prediction_model``.
- Softmax / class selection stay in the prediction engine.

Run::

    python -m src.gradcam path/to/wafer.jpg
"""

from __future__ import annotations

import base64
import io
import logging
import time
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import Tensor
from torch.nn import Module

from .config import PROJECT_ROOT
from .predict import (
    PredictionError,
    get_prediction_device,
    get_prediction_model,
    load_prediction_model,
    predict_api,
)
from .preprocess import (
    CorruptedImageError,
    MissingFileError,
    PreprocessError,
    UnsupportedFormatError,
    load_image,
    preprocess_image,
    resize_rgb_to_img_size,
)
from .wafer_constants import IMG_SIZE

logger = logging.getLogger(__name__)

GRADCAM_RESULTS_DIR: Path = PROJECT_ROOT / "gradcam_results"
DEFAULT_TARGET_LAYER: str = "layer4"
DEFAULT_OVERLAY_ALPHA: float = 0.45


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class GradCAMError(Exception):
    """Base exception for Grad-CAM failures."""


class InvalidTargetLayerError(GradCAMError):
    """Raised when the configured target layer cannot be resolved."""


class InvalidTensorShapeError(GradCAMError):
    """Raised when activation / gradient tensors have unexpected shapes."""


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------


def encode_base64(image: np.ndarray | Image.Image, *, format: str = "PNG") -> str:
    """Encode an RGB image (NumPy or PIL) as a base64 PNG/JPEG string."""
    if isinstance(image, np.ndarray):
        pil_image = Image.fromarray(_ensure_uint8_rgb(image), mode="RGB")
    elif isinstance(image, Image.Image):
        pil_image = image.convert("RGB")
    else:
        raise GradCAMError(f"Unsupported image type for base64 encoding: {type(image)!r}")

    buffer = io.BytesIO()
    pil_image.save(buffer, format=format)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _ensure_uint8_rgb(image: np.ndarray) -> np.ndarray:
    """Convert an array to contiguous uint8 RGB ``(H, W, 3)``."""
    if image.ndim != 3 or image.shape[2] != 3:
        raise GradCAMError(f"Expected RGB array (H, W, 3); got shape={image.shape}.")
    if image.dtype == np.uint8:
        return np.ascontiguousarray(image)
    array = image.astype(np.float32)
    max_value = float(array.max()) if array.size else 1.0
    if max_value <= 1.0:
        array = array * 255.0
    return np.clip(array, 0, 255).astype(np.uint8)


def _to_pil_rgb(image: str | Path | Image.Image | np.ndarray) -> Image.Image:
    """Convert supported inputs to an RGB PIL image."""
    try:
        if isinstance(image, Image.Image):
            pil = image.convert("RGB")
        elif isinstance(image, np.ndarray):
            if image.size == 0:
                raise GradCAMError("Empty numpy image.")
            if image.ndim != 3 or image.shape[2] != 3:
                raise GradCAMError(
                    f"Expected RGB numpy array (H, W, 3); got {image.shape}."
                )
            pil = Image.fromarray(_ensure_uint8_rgb(image), mode="RGB")
        elif isinstance(image, (str, Path)):
            pil = load_image(image)
        else:
            raise GradCAMError(
                f"Unsupported input type: {type(image)!r}. "
                "Expected path, PIL.Image, or numpy.ndarray."
            )
    except (UnsupportedFormatError, MissingFileError, CorruptedImageError) as exc:
        raise GradCAMError(str(exc)) from exc
    except PreprocessError as exc:
        raise GradCAMError(f"Failed to load image: {exc}") from exc

    if pil.size[0] <= 0 or pil.size[1] <= 0:
        raise GradCAMError(f"Empty image with invalid size: {pil.size}.")
    return pil


def _display_rgb(image: str | Path | Image.Image | np.ndarray) -> np.ndarray:
    """Return canonical 224×224 uint8 RGB (shared with die overlay / density)."""
    return resize_rgb_to_img_size(image)


# ---------------------------------------------------------------------------
# Overlay / colormap
# ---------------------------------------------------------------------------


def generate_overlay(
    original_rgb: np.ndarray,
    heatmap: np.ndarray,
    *,
    alpha: float = DEFAULT_OVERLAY_ALPHA,
) -> np.ndarray:
    """
    Blend a Grad-CAM heatmap onto the original RGB image.

    Args:
        original_rgb: uint8 RGB image ``(H, W, 3)``.
        heatmap: float heatmap in ``[0, 1]`` shaped ``(H, W)`` or ``(H, W, 1)``.
        alpha: Heatmap opacity (default ``0.45``).
    """
    if not 0.0 <= alpha <= 1.0:
        raise GradCAMError(f"alpha must be in [0, 1]; got {alpha}.")

    original = _ensure_uint8_rgb(original_rgb)
    heat = np.asarray(heatmap, dtype=np.float32)
    if heat.ndim == 3 and heat.shape[2] == 1:
        heat = heat[:, :, 0]
    if heat.ndim != 2:
        raise GradCAMError(f"Heatmap must be 2-D; got shape={heat.shape}.")

    if heat.shape[:2] != original.shape[:2]:
        heat = cv2.resize(heat, (original.shape[1], original.shape[0]), interpolation=cv2.INTER_LINEAR)

    heat = np.clip(heat, 0.0, 1.0)
    heat_uint8 = np.uint8(heat * 255.0)
    colored = cv2.applyColorMap(heat_uint8, cv2.COLORMAP_JET)
    colored = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)

    overlay = (
        (1.0 - alpha) * original.astype(np.float32) + alpha * colored.astype(np.float32)
    )
    return np.clip(overlay, 0, 255).astype(np.uint8)


def _heatmap_to_rgb(heatmap: np.ndarray) -> np.ndarray:
    """Convert a ``[0, 1]`` heatmap to a JET colormap RGB image."""
    heat = np.clip(np.asarray(heatmap, dtype=np.float32), 0.0, 1.0)
    if heat.ndim != 2:
        raise GradCAMError(f"Heatmap must be 2-D; got shape={heat.shape}.")
    heat_uint8 = np.uint8(heat * 255.0)
    colored_bgr = cv2.applyColorMap(heat_uint8, cv2.COLORMAP_JET)
    return cv2.cvtColor(colored_bgr, cv2.COLOR_BGR2RGB)


def _make_combined(
    original: np.ndarray,
    heatmap_rgb: np.ndarray,
    overlay: np.ndarray,
) -> np.ndarray:
    """Stack original | heatmap | overlay horizontally."""
    return np.concatenate(
        [
            _ensure_uint8_rgb(original),
            _ensure_uint8_rgb(heatmap_rgb),
            _ensure_uint8_rgb(overlay),
        ],
        axis=1,
    )


# ---------------------------------------------------------------------------
# GradCAM engine
# ---------------------------------------------------------------------------


class GradCAM:
    """
    Grad-CAM generator for ``WaferClassifier`` (ResNet50 ``layer4`` by default).

    Prediction labels/confidence always come from ``predict.py``.
    """

    def __init__(
        self,
        *,
        target_layer: str = DEFAULT_TARGET_LAYER,
        alpha: float = DEFAULT_OVERLAY_ALPHA,
    ) -> None:
        load_prediction_model()
        self.model = get_prediction_model()
        self.device = get_prediction_device()
        self.target_layer_name = target_layer
        self.alpha = alpha
        self._target_module = self._resolve_target_layer(target_layer)
        self._activations: Tensor | None = None
        self._gradients: Tensor | None = None
        self._handles: list[Any] = []

    def _resolve_target_layer(self, layer_name: str) -> Module:
        """Resolve a dotted layer name under ``model.backbone`` (e.g. ``layer4``)."""
        module: Module | Any = self.model.backbone
        try:
            for part in layer_name.split("."):
                module = getattr(module, part)
        except AttributeError as exc:
            raise InvalidTargetLayerError(
                f"Invalid Grad-CAM target layer '{layer_name}' on ResNet50 backbone."
            ) from exc
        if not isinstance(module, Module):
            raise InvalidTargetLayerError(
                f"Target '{layer_name}' is not an nn.Module."
            )
        return module

    def _register_hooks(self) -> None:
        """Attach forward/backward hooks to capture activations and gradients."""

        def _forward_hook(_module: Module, _inputs: tuple[Any, ...], output: Tensor) -> None:
            self._activations = output.detach()

        def _backward_hook(
            _module: Module,
            _grad_input: tuple[Tensor | None, ...],
            grad_output: tuple[Tensor | None, ...],
        ) -> None:
            if grad_output[0] is None:
                raise GradCAMError("Backward hook received empty gradients.")
            self._gradients = grad_output[0].detach()

        self._handles = [
            self._target_module.register_forward_hook(_forward_hook),
            self._target_module.register_full_backward_hook(_backward_hook),
        ]

    def _remove_hooks(self) -> None:
        for handle in self._handles:
            handle.remove()
        self._handles = []

    def _compute_cam(
        self,
        class_index: int,
        input_tensor: Tensor,
        *,
        output_size: int | None = IMG_SIZE,
    ) -> np.ndarray:
        """
        Compute a normalized Grad-CAM heatmap for ``class_index``.

        Returns a normalized float32 array in ``[0, 1]``. By default it is
        bilinear-upsampled to ``IMG_SIZE`` for legacy image outputs. Pass
        ``output_size=None`` to preserve the native target-layer CAM grid
        (ResNet50 layer4 is typically 7×7) for client-side/WebGL rendering.
        """
        if input_tensor.ndim != 4 or input_tensor.shape[0] != 1:
            raise InvalidTensorShapeError(
                f"Expected input tensor (1, 3, H, W); got {tuple(input_tensor.shape)}."
            )

        self.model.eval()
        self._activations = None
        self._gradients = None
        self._register_hooks()

        try:
            input_tensor = input_tensor.to(self.device)
            input_tensor.requires_grad_(True)

            logits = self.model(input_tensor)
            if logits.ndim != 2 or class_index < 0 or class_index >= logits.shape[1]:
                raise GradCAMError(
                    f"Invalid class_index={class_index} for logits shape {tuple(logits.shape)}."
                )

            self.model.zero_grad(set_to_none=True)
            score = logits[0, class_index]
            score.backward()

            if self._activations is None or self._gradients is None:
                raise GradCAMError("Failed to capture activations or gradients.")

            activations = self._activations
            gradients = self._gradients
            if activations.shape != gradients.shape:
                raise InvalidTensorShapeError(
                    f"Activation/gradient shape mismatch: "
                    f"{tuple(activations.shape)} vs {tuple(gradients.shape)}."
                )

            weights = gradients.mean(dim=(2, 3), keepdim=True)
            cam = (weights * activations).sum(dim=1, keepdim=True)
            cam = F.relu(cam)
            if output_size is not None:
                if int(output_size) <= 0:
                    raise GradCAMError(
                        f"output_size must be positive or None; got {output_size}."
                    )
                cam = F.interpolate(
                    cam,
                    size=(int(output_size), int(output_size)),
                    mode="bilinear",
                    align_corners=False,
                )
            cam = cam[0, 0].detach().cpu().numpy().astype(np.float32)
            cam_min, cam_max = float(cam.min()), float(cam.max())
            if cam_max > cam_min:
                cam = (cam - cam_min) / (cam_max - cam_min)
            else:
                cam = np.zeros_like(cam, dtype=np.float32)
            return np.clip(cam, 0.0, 1.0)
        finally:
            self._remove_hooks()
            self.model.zero_grad(set_to_none=True)

    def generate(
        self,
        image: str | Path | Image.Image | np.ndarray,
        *,
        save: bool = True,
        output_dir: Path | str | None = None,
        alpha: float | None = None,
    ) -> dict[str, Any]:
        """
        Generate Grad-CAM artifacts for one image.

        Prediction is obtained exclusively from ``predict_api``.
        """
        start = time.perf_counter()
        alpha_value = self.alpha if alpha is None else float(alpha)

        # 1) Single prediction via the shared prediction engine
        try:
            prediction = predict_api(image)
        except PredictionError as exc:
            raise GradCAMError(f"Prediction failed before Grad-CAM: {exc}") from exc
        if isinstance(prediction, list):
            raise GradCAMError("Expected a single-image prediction result.")

        class_index = int(prediction["class_index"])
        defect_type = str(prediction["defect_type"])
        confidence = float(prediction["confidence"])

        # 2) Display RGB + model tensor
        original = _display_rgb(image)
        try:
            tensor = preprocess_image(image, augment=False).unsqueeze(0)
        except PreprocessError as exc:
            raise GradCAMError(f"Preprocessing failed for Grad-CAM: {exc}") from exc

        # 3) Grad-CAM heatmap for the predicted class only
        heatmap = self._compute_cam(class_index, tensor)
        heatmap_rgb = _heatmap_to_rgb(heatmap)
        overlay = generate_overlay(original, heatmap, alpha=alpha_value)
        combined = _make_combined(original, heatmap_rgb, overlay)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        result: dict[str, Any] = {
            "prediction": {
                "class": defect_type,
                "class_index": class_index,
                "confidence": confidence,
            },
            "gradcam": {
                "layer": self.target_layer_name,
                "heatmap": encode_base64(heatmap_rgb),
                "overlay": encode_base64(overlay),
                "original": encode_base64(original),
                "combined": encode_base64(combined),
            },
            "arrays": {
                "original": original,
                "heatmap": heatmap,
                "heatmap_rgb": heatmap_rgb,
                "overlay": overlay,
                "combined": combined,
            },
            "pil": {
                "original": Image.fromarray(original, mode="RGB"),
                "heatmap": Image.fromarray(heatmap_rgb, mode="RGB"),
                "overlay": Image.fromarray(overlay, mode="RGB"),
                "combined": Image.fromarray(combined, mode="RGB"),
            },
            "target_layer": self.target_layer_name,
            "inference_time_ms": round(elapsed_ms, 4),
            "heatmap_size": [int(heatmap.shape[0]), int(heatmap.shape[1])],
            "overlay_size": [int(overlay.shape[0]), int(overlay.shape[1])],
            "alpha": alpha_value,
        }

        saved_files: dict[str, str] = {}
        if save:
            saved_files = save_gradcam(result, output_dir=output_dir)
            result["saved_files"] = saved_files

        _print_gradcam_summary(result, saved_files)
        return result


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


def generate_gradcam(
    image: str | Path | Image.Image | np.ndarray,
    *,
    target_layer: str = DEFAULT_TARGET_LAYER,
    alpha: float = DEFAULT_OVERLAY_ALPHA,
    save: bool = True,
    output_dir: Path | str | None = None,
) -> dict[str, Any]:
    """
    Generate Grad-CAM for a single image.

    Uses ``predict_api`` for the class prediction, then computes the heatmap
    for that class with the singleton ``WaferClassifier``.
    """
    engine = GradCAM(target_layer=target_layer, alpha=alpha)
    return engine.generate(image, save=save, output_dir=output_dir, alpha=alpha)


def batch_gradcam(
    images: Sequence[str | Path | Image.Image | np.ndarray],
    *,
    target_layer: str = DEFAULT_TARGET_LAYER,
    alpha: float = DEFAULT_OVERLAY_ALPHA,
    save: bool = True,
    output_dir: Path | str | None = None,
) -> list[dict[str, Any]]:
    """Generate Grad-CAM results for multiple images."""
    if not images:
        raise GradCAMError("batch_gradcam requires at least one image.")

    engine = GradCAM(target_layer=target_layer, alpha=alpha)
    base_dir = Path(output_dir) if output_dir is not None else GRADCAM_RESULTS_DIR
    results: list[dict[str, Any]] = []

    for index, image in enumerate(images):
        item_dir = base_dir / f"sample_{index:04d}" if save else None
        results.append(
            engine.generate(
                image,
                save=save,
                output_dir=item_dir,
                alpha=alpha,
            )
        )
    return results


def save_gradcam(
    result: dict[str, Any],
    *,
    output_dir: Path | str | None = None,
) -> dict[str, str]:
    """
    Save ``original.png``, ``heatmap.png``, ``overlay.png``, ``combined.png``.

    Returns a mapping of artifact name → absolute path.
    """
    destination = Path(output_dir) if output_dir is not None else GRADCAM_RESULTS_DIR
    destination.mkdir(parents=True, exist_ok=True)

    arrays = result.get("arrays") or {}
    required = ("original", "heatmap_rgb", "overlay", "combined")
    for key in required:
        if key not in arrays and key == "heatmap_rgb" and "heatmap" in arrays:
            # allow callers that only stored float heatmap
            arrays["heatmap_rgb"] = _heatmap_to_rgb(arrays["heatmap"])
        if key not in arrays:
            raise GradCAMError(f"Cannot save Grad-CAM result; missing array '{key}'.")

    paths = {
        "original": destination / "original.png",
        "heatmap": destination / "heatmap.png",
        "overlay": destination / "overlay.png",
        "combined": destination / "combined.png",
    }
    Image.fromarray(_ensure_uint8_rgb(arrays["original"]), mode="RGB").save(paths["original"])
    Image.fromarray(_ensure_uint8_rgb(arrays["heatmap_rgb"]), mode="RGB").save(paths["heatmap"])
    Image.fromarray(_ensure_uint8_rgb(arrays["overlay"]), mode="RGB").save(paths["overlay"])
    Image.fromarray(_ensure_uint8_rgb(arrays["combined"]), mode="RGB").save(paths["combined"])

    return {name: str(path.resolve()) for name, path in paths.items()}


def _print_gradcam_summary(
    result: dict[str, Any],
    saved_files: dict[str, str],
) -> None:
    """Print the Grad-CAM terminal summary block."""
    prediction = result.get("prediction") or {}
    print("=" * 50)
    print("GRAD-CAM GENERATED")
    print("=" * 50)
    print(f"Prediction     : {prediction.get('class')}")
    print(f"Confidence     : {float(prediction.get('confidence', 0.0)):.2f}%")
    print(f"Target Layer   : {result.get('target_layer')}")
    print(f"Heatmap Size   : {result.get('heatmap_size')}")
    print(f"Overlay Size   : {result.get('overlay_size')}")
    if saved_files:
        print("Saved Files    :")
        for name, path in saved_files.items():
            print(f"  - {name}: {path}")
    print("=" * 50)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint: ``python -m src.gradcam <image_path>``."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m src.gradcam <image_path>")
        return 1

    generate_gradcam(args[0], save=True)
    return 0


__all__ = [
    "GradCAMError",
    "InvalidTargetLayerError",
    "InvalidTensorShapeError",
    "GRADCAM_RESULTS_DIR",
    "DEFAULT_TARGET_LAYER",
    "DEFAULT_OVERLAY_ALPHA",
    "GradCAM",
    "generate_gradcam",
    "generate_overlay",
    "save_gradcam",
    "encode_base64",
    "batch_gradcam",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
