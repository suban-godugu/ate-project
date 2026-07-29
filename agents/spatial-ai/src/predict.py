"""
Prediction engine for WaferVision-AI.

Responsibility: single source of truth for wafer defect inference.
All future modules (FastAPI, Grad-CAM, pipeline, batch analysis) MUST call
this module instead of implementing their own prediction logic.

Reuses ``load_model`` from ``model.py`` and ``preprocess_image`` from
``preprocess.py``. Softmax is applied here only — the model still returns
raw logits.

Run a single-image demo::

    python -m src.predict path/to/wafer.jpg
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torch import Tensor

from .config import MODEL_PATH
from .model import (
    MissingModelFileError,
    ModelError,
    WaferClassifier,
    get_device,
    load_model,
)
from .preprocess import (
    CorruptedImageError,
    MissingFileError,
    PreprocessError,
    UnsupportedFormatError,
    load_image,
    preprocess_image,
    preprocess_image_batch,
)
from .wafer_constants import (
    DEFECT_CLASSES,
    IDX_TO_CLASS,
    IMG_SIZE,
    NUM_CLASSES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Singleton model state
# ---------------------------------------------------------------------------

_MODEL: WaferClassifier | None = None
_DEVICE: torch.device | None = None
_MODEL_PATH: Path | None = None
_MODEL_LOCK = threading.Lock()
_WAFER_TRAINED: bool = False

TOP_K_DEFAULT: int = 3


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PredictionError(Exception):
    """Base exception for prediction engine failures."""


class EmptyImageError(PredictionError):
    """Raised when an image has no usable pixels."""


class InvalidImageShapeError(PredictionError):
    """Raised when image channels / dimensions are invalid."""


# ---------------------------------------------------------------------------
# Model singleton
# ---------------------------------------------------------------------------


def load_prediction_model(
    model_path: Path | str = MODEL_PATH,
    *,
    device: torch.device | str | None = None,
    force_reload: bool = False,
) -> WaferClassifier:
    """
    Load the wafer classifier once and reuse it for all predictions.

    Subsequent calls return the cached model unless ``force_reload`` is True.
    """
    global _MODEL, _DEVICE, _MODEL_PATH, _WAFER_TRAINED

    resolved_path = Path(model_path)
    with _MODEL_LOCK:
        if (
            not force_reload
            and _MODEL is not None
            and _MODEL_PATH == resolved_path
            and (device is None or _DEVICE == torch.device(device))
        ):
            return _MODEL

        target = get_device() if device is None else torch.device(device)
        try:
            from .model import _load_checkpoint_file

            raw_checkpoint = _load_checkpoint_file(resolved_path)
            model = load_model(
                resolved_path,
                device=target,
                pretrained_backbone=False,
                freeze_backbone=True,
                eval_mode=True,
            )
        except (MissingModelFileError, ModelError) as exc:
            raise PredictionError(f"Failed to load prediction model: {exc}") from exc

        # Grad-CAM is only meaningful for a wafer-trained fine-tune, not ImageNet bootstrap.
        wafer_trained = False
        if isinstance(raw_checkpoint, Mapping):
            if "wafer_trained" in raw_checkpoint:
                wafer_trained = bool(raw_checkpoint.get("wafer_trained"))
            else:
                epoch = raw_checkpoint.get("epoch")
                val_acc = raw_checkpoint.get("val_accuracy")
                try:
                    wafer_trained = int(epoch or 0) > 0 and float(val_acc or 0.0) > 0.55
                except (TypeError, ValueError):
                    wafer_trained = False

        _MODEL = model
        _DEVICE = target
        _MODEL_PATH = resolved_path
        _WAFER_TRAINED = wafer_trained
        logger.info(
            "Prediction model loaded once from %s on %s (wafer_trained=%s)",
            resolved_path,
            target,
            wafer_trained,
        )
        return _MODEL


def is_wafer_trained_model() -> bool:
    """True when checkpoint is a real wafer fine-tune (Grad-CAM allowed)."""
    if _MODEL is None:
        load_prediction_model()
    return bool(_WAFER_TRAINED)


def get_prediction_model() -> WaferClassifier:
    """Return the cached model, loading the default checkpoint if needed."""
    if _MODEL is None:
        return load_prediction_model()
    return _MODEL


def get_prediction_device() -> torch.device:
    """Return the device used by the singleton prediction model."""
    if _DEVICE is None:
        load_prediction_model()
    assert _DEVICE is not None
    return _DEVICE


def reset_prediction_model() -> None:
    """Clear the singleton cache (primarily for tests)."""
    global _MODEL, _DEVICE, _MODEL_PATH, _WAFER_TRAINED
    with _MODEL_LOCK:
        _MODEL = None
        _DEVICE = None
        _MODEL_PATH = None
        _WAFER_TRAINED = False


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------


def _validate_pil_image(image: Image.Image) -> Image.Image:
    """Validate a PIL image and return an RGB copy."""
    if not isinstance(image, Image.Image):
        raise PredictionError(f"Expected PIL.Image, got {type(image)!r}.")
    if image.size[0] <= 0 or image.size[1] <= 0:
        raise EmptyImageError(
            f"Empty image with invalid size: {image.size}."
        )
    rgb = image.convert("RGB")
    if min(rgb.size) <= 0:
        raise EmptyImageError("Image has no usable spatial dimensions.")
    return rgb


def _validate_numpy_image(array: np.ndarray) -> np.ndarray:
    """Validate a NumPy RGB array."""
    if not isinstance(array, np.ndarray):
        raise PredictionError(f"Expected numpy.ndarray, got {type(array)!r}.")
    if array.size == 0:
        raise EmptyImageError("Empty numpy image array.")
    if array.ndim != 3:
        raise InvalidImageShapeError(
            f"Expected RGB array with shape (H, W, 3); got ndim={array.ndim}."
        )
    if array.shape[2] != 3:
        raise InvalidImageShapeError(
            f"Expected 3 channels (RGB); got shape={array.shape}."
        )
    if array.shape[0] <= 0 or array.shape[1] <= 0:
        raise EmptyImageError(f"Invalid spatial dimensions: {array.shape}.")
    return array


# ---------------------------------------------------------------------------
# Core inference
# ---------------------------------------------------------------------------


def _prepare_batch_tensor(
    images: Sequence[Any],
    device: torch.device,
) -> Tensor:
    """Preprocess one or more images into a batch tensor on ``device``."""
    if not images:
        raise PredictionError("Cannot predict on an empty image list.")

    try:
        if len(images) == 1:
            tensor = preprocess_image(images[0], augment=False).unsqueeze(0)
        else:
            tensor = preprocess_image_batch(images, augment=False)
    except UnsupportedFormatError as exc:
        raise PredictionError(f"Unsupported image format: {exc}") from exc
    except MissingFileError as exc:
        raise PredictionError(f"Image file not found: {exc}") from exc
    except CorruptedImageError as exc:
        raise PredictionError(f"Corrupted image: {exc}") from exc
    except PreprocessError as exc:
        message = str(exc)
        if "shape" in message.lower() or "channel" in message.lower():
            raise InvalidImageShapeError(message) from exc
        raise PredictionError(f"Preprocessing failed: {exc}") from exc

    if tensor.ndim != 4 or tensor.shape[1:] != (3, IMG_SIZE, IMG_SIZE):
        raise InvalidImageShapeError(
            f"Expected batch tensor (N, 3, {IMG_SIZE}, {IMG_SIZE}); "
            f"got {tuple(tensor.shape)}."
        )
    return tensor.to(device, non_blocking=device.type == "cuda")


def _topk_from_probabilities(
    probabilities: Tensor,
    *,
    top_k: int = TOP_K_DEFAULT,
) -> list[dict[str, Any]]:
    """Build top-k prediction entries with percentage confidences."""
    k = min(int(top_k), int(probabilities.numel()))
    values, indices = torch.topk(probabilities, k=k)
    results: list[dict[str, Any]] = []
    for confidence, class_index in zip(
        values.tolist(), indices.tolist(), strict=True
    ):
        index = int(class_index)
        results.append(
            {
                "class": IDX_TO_CLASS[index],
                "class_index": index,
                "confidence": round(float(confidence) * 100.0, 4),
            }
        )
    return results


def _probabilities_dict(probabilities: Tensor) -> dict[str, float]:
    """Map every defect class name to a percentage probability."""
    values = probabilities.detach().cpu().tolist()
    if len(values) != NUM_CLASSES:
        raise PredictionError(
            f"Expected {NUM_CLASSES} probabilities; got {len(values)}."
        )
    return {
        IDX_TO_CLASS[index]: round(float(values[index]) * 100.0, 4)
        for index in range(NUM_CLASSES)
    }


def _build_prediction_result(
    probabilities: Tensor,
    *,
    inference_time_ms: float,
    input_type: str,
    image_size: tuple[int, int] | None,
    top_k: int = TOP_K_DEFAULT,
) -> dict[str, Any]:
    """Assemble the reusable JSON prediction payload."""
    class_index = int(torch.argmax(probabilities).item())
    confidence = float(probabilities[class_index].item()) * 100.0
    return {
        "class_index": class_index,
        "defect_type": IDX_TO_CLASS[class_index],
        "confidence": round(confidence, 4),
        "top_predictions": _topk_from_probabilities(probabilities, top_k=top_k),
        "probabilities": _probabilities_dict(probabilities),
        "inference_time_ms": round(float(inference_time_ms), 4),
        "input_type": input_type,
        "image_size": (
            {"width": image_size[0], "height": image_size[1]}
            if image_size is not None
            else None
        ),
        "model_input_size": IMG_SIZE,
        "num_classes": NUM_CLASSES,
        "class_names": list(DEFECT_CLASSES),
    }


def _predict_tensor_batch(
    batch: Tensor,
    model: WaferClassifier,
    *,
    top_k: int,
    input_types: Sequence[str],
    image_sizes: Sequence[tuple[int, int] | None],
) -> list[dict[str, Any]]:
    """Run a forward pass on a preprocessed batch and build JSON results."""
    model.eval()
    start = time.perf_counter()
    with torch.no_grad():
        logits = model(batch)
        if logits.ndim != 2 or logits.shape[1] != NUM_CLASSES:
            raise PredictionError(
                f"Unexpected logits shape {tuple(logits.shape)}; "
                f"expected (N, {NUM_CLASSES})."
            )
        probabilities = F.softmax(logits, dim=1)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    per_image_ms = elapsed_ms / float(batch.size(0))

    results: list[dict[str, Any]] = []
    for row in range(batch.size(0)):
        results.append(
            _build_prediction_result(
                probabilities[row],
                inference_time_ms=per_image_ms,
                input_type=input_types[row],
                image_size=image_sizes[row],
                top_k=top_k,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Public prediction API
# ---------------------------------------------------------------------------


def predict_pil(
    image: Image.Image,
    *,
    top_k: int = TOP_K_DEFAULT,
    verbose: bool = False,
) -> dict[str, Any]:
    """Predict defect class from a PIL image."""
    validated = _validate_pil_image(image)
    model = get_prediction_model()
    device = get_prediction_device()
    batch = _prepare_batch_tensor([validated], device)
    results = _predict_tensor_batch(
        batch,
        model,
        top_k=top_k,
        input_types=["PIL Image"],
        image_sizes=[validated.size],
    )
    result = results[0]
    if verbose:
        print_prediction(result)
    return result


def predict_numpy(
    array: np.ndarray,
    *,
    top_k: int = TOP_K_DEFAULT,
    verbose: bool = False,
) -> dict[str, Any]:
    """Predict defect class from a NumPy RGB array shaped ``(H, W, 3)``."""
    validated = _validate_numpy_image(array)
    model = get_prediction_model()
    device = get_prediction_device()
    batch = _prepare_batch_tensor([validated], device)
    results = _predict_tensor_batch(
        batch,
        model,
        top_k=top_k,
        input_types=["NumPy RGB Array"],
        image_sizes=[(int(validated.shape[1]), int(validated.shape[0]))],
    )
    result = results[0]
    if verbose:
        print_prediction(result)
    return result


def predict_image(
    image: str | Path | Image.Image | np.ndarray,
    *,
    top_k: int = TOP_K_DEFAULT,
    verbose: bool = True,
) -> dict[str, Any]:
    """
    Predict defect class from a path, PIL image, or NumPy RGB array.

    This is the primary entrypoint for single-image inference.
    """
    if isinstance(image, Image.Image):
        return predict_pil(image, top_k=top_k, verbose=verbose)
    if isinstance(image, np.ndarray):
        return predict_numpy(image, top_k=top_k, verbose=verbose)
    if isinstance(image, (str, Path)):
        path = Path(image)
        try:
            pil_image = load_image(path)
        except UnsupportedFormatError as exc:
            raise PredictionError(f"Unsupported image format: {exc}") from exc
        except MissingFileError as exc:
            raise PredictionError(f"Image file not found: {exc}") from exc
        except CorruptedImageError as exc:
            raise PredictionError(f"Corrupted image: {exc}") from exc
        except PreprocessError as exc:
            raise PredictionError(f"Failed to load image: {exc}") from exc

        model = get_prediction_model()
        device = get_prediction_device()
        batch = _prepare_batch_tensor([pil_image], device)
        results = _predict_tensor_batch(
            batch,
            model,
            top_k=top_k,
            input_types=["Image Path"],
            image_sizes=[pil_image.size],
        )
        result = results[0]
        result["source_path"] = str(path)
        if verbose:
            print_prediction(result)
        return result

    raise PredictionError(
        f"Unsupported input type: {type(image)!r}. "
        "Expected path, PIL.Image, or numpy.ndarray."
    )


def predict_batch(
    images: Sequence[str | Path | Image.Image | np.ndarray],
    *,
    top_k: int = TOP_K_DEFAULT,
    verbose: bool = False,
) -> list[dict[str, Any]]:
    """
    Predict defect classes for multiple images in one forward pass.

    Returns a list of JSON prediction dictionaries.
    """
    if not images:
        raise PredictionError("predict_batch requires at least one image.")

    prepared: list[Any] = []
    input_types: list[str] = []
    image_sizes: list[tuple[int, int] | None] = []

    for item in images:
        if isinstance(item, Image.Image):
            validated = _validate_pil_image(item)
            prepared.append(validated)
            input_types.append("PIL Image")
            image_sizes.append(validated.size)
        elif isinstance(item, np.ndarray):
            validated_arr = _validate_numpy_image(item)
            prepared.append(validated_arr)
            input_types.append("NumPy RGB Array")
            image_sizes.append(
                (int(validated_arr.shape[1]), int(validated_arr.shape[0]))
            )
        elif isinstance(item, (str, Path)):
            try:
                pil_image = load_image(item)
            except UnsupportedFormatError as exc:
                raise PredictionError(f"Unsupported image format: {exc}") from exc
            except MissingFileError as exc:
                raise PredictionError(f"Image file not found: {exc}") from exc
            except CorruptedImageError as exc:
                raise PredictionError(f"Corrupted image: {exc}") from exc
            prepared.append(pil_image)
            input_types.append("Image Path")
            image_sizes.append(pil_image.size)
        else:
            raise PredictionError(
                f"Unsupported batch item type: {type(item)!r}."
            )

    model = get_prediction_model()
    device = get_prediction_device()
    batch = _prepare_batch_tensor(prepared, device)
    results = _predict_tensor_batch(
        batch,
        model,
        top_k=top_k,
        input_types=input_types,
        image_sizes=image_sizes,
    )

    for index, item in enumerate(images):
        if isinstance(item, (str, Path)):
            results[index]["source_path"] = str(item)

    if verbose:
        for result in results:
            print_prediction(result)
    return results


def predict_api(
    image: str | Path | Image.Image | np.ndarray | Sequence[Any],
    *,
    top_k: int = TOP_K_DEFAULT,
) -> dict[str, Any] | list[dict[str, Any]]:
    """
    FastAPI-ready prediction entrypoint.

    Accepts a single image or a sequence of images and returns JSON-serializable
    prediction result(s) without printing to the terminal.
    """
    if isinstance(image, (list, tuple)):
        return predict_batch(image, top_k=top_k, verbose=False)
    return predict_image(image, top_k=top_k, verbose=False)


# ---------------------------------------------------------------------------
# Terminal formatting
# ---------------------------------------------------------------------------


def print_prediction(result: Mapping[str, Any]) -> None:
    """Pretty-print a prediction result to the terminal."""
    image_size = result.get("image_size")
    if isinstance(image_size, dict):
        size_text = f"{image_size.get('width')} x {image_size.get('height')}"
    else:
        size_text = "N/A"

    print("=" * 50)
    print("WAFER AI PREDICTION RESULT")
    print("=" * 50)
    print(f"Input Type      : {result.get('input_type', 'N/A')}")
    print(f"Image Size      : {size_text}")
    print(f"Class Index     : {result.get('class_index')}")
    print(f"Defect Type     : {result.get('defect_type')}")
    print(f"Confidence      : {float(result.get('confidence', 0.0)):.2f}%")
    print(f"Inference Time  : {float(result.get('inference_time_ms', 0.0)):.2f} ms")
    print("=" * 50)
    print("ALL CLASS PROBABILITIES")
    print("=" * 50)

    probabilities = result.get("probabilities") or {}
    predicted = result.get("defect_type")
    for class_name in DEFECT_CLASSES:
        value = float(probabilities.get(class_name, 0.0))
        marker = "  <-- MAX" if class_name == predicted else ""
        print(f"{class_name:12s} {value:6.2f}%{marker}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint: ``python -m src.predict <image_path>``."""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = list(sys.argv[1:] if argv is None else argv)
    if not args:
        print("Usage: python -m src.predict <image_path>")
        return 1

    load_prediction_model()
    predict_image(args[0], verbose=True)
    return 0


__all__ = [
    "PredictionError",
    "EmptyImageError",
    "InvalidImageShapeError",
    "load_prediction_model",
    "is_wafer_trained_model",
    "get_prediction_model",
    "get_prediction_device",
    "reset_prediction_model",
    "predict_image",
    "predict_numpy",
    "predict_pil",
    "predict_batch",
    "predict_api",
    "print_prediction",
    "main",
    "TOP_K_DEFAULT",
]


if __name__ == "__main__":
    raise SystemExit(main())
