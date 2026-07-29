"""
Image preprocessing and dataset pipeline for WaferVision-AI.

Responsibility: image loading, validation, resizing, normalization, tensor
conversion, wafer mask creation, reusable transforms, Dataset / DataLoader
construction.

No model code. No API code. No inference.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Iterator, Sequence

import numpy as np
from PIL import Image, UnidentifiedImageError
from torch import Tensor
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

from .config import DATASET_ROOT, TEST_DIR, TRAIN_DIR, VALID_DIR
from .wafer_constants import (
    AUG_BRIGHTNESS,
    AUG_CONTRAST,
    AUG_HORIZONTAL_FLIP_PROB,
    AUG_ROTATION_DEGREES,
    AUG_SATURATION,
    AUG_SCALE,
    AUG_TRANSLATE,
    CENTER_X,
    CENTER_Y,
    CLASS_TO_IDX,
    DEFAULT_BATCH_SIZE,
    DEFAULT_NUM_WORKERS,
    DEFAULT_PIN_MEMORY,
    DEFECT_CLASSES,
    IDX_TO_CLASS,
    IMAGENET_MEAN,
    IMAGENET_STD,
    IMG_SIZE,
    SUPPORTED_IMAGE_EXTENSIONS,
    WAFER_RADIUS,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PreprocessError(Exception):
    """Base exception for preprocessing / dataset failures."""


class MissingFileError(PreprocessError):
    """Raised when an expected image or directory path is missing."""


class UnsupportedFormatError(PreprocessError):
    """Raised when an image format is not supported."""


class CorruptedImageError(PreprocessError):
    """Raised when an image cannot be decoded."""


class EmptyDirectoryError(PreprocessError):
    """Raised when a dataset split or class folder contains no images."""


class InvalidClassLabelError(PreprocessError):
    """Raised when a class folder name is not in the canonical mapping."""


# ---------------------------------------------------------------------------
# Image loading & validation
# ---------------------------------------------------------------------------


def is_supported_image(path: Path | str) -> bool:
    """Return True if ``path`` has a supported image extension."""
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def validate_image_path(path: Path | str) -> Path:
    """
    Validate that ``path`` exists and has a supported image extension.

    Raises:
        MissingFileError: If the file does not exist.
        UnsupportedFormatError: If the extension is not supported.
    """
    image_path = Path(path)
    if not image_path.is_file():
        raise MissingFileError(f"Image file not found: {image_path}")
    if not is_supported_image(image_path):
        raise UnsupportedFormatError(
            f"Unsupported image format '{image_path.suffix}' for file: "
            f"{image_path}. Supported formats: "
            f"{sorted(SUPPORTED_IMAGE_EXTENSIONS)}"
        )
    return image_path


def load_image(path: Path | str) -> Image.Image:
    """
    Load an image from disk with PIL and convert it to RGB.

    Raises:
        MissingFileError: If the file does not exist.
        UnsupportedFormatError: If the extension is not supported.
        CorruptedImageError: If the image cannot be decoded.
    """
    image_path = validate_image_path(path)
    try:
        with Image.open(image_path) as image:
            image.load()
            return image.convert("RGB")
    except UnidentifiedImageError as exc:
        raise CorruptedImageError(
            f"Unable to identify image file: {image_path}"
        ) from exc
    except OSError as exc:
        raise CorruptedImageError(
            f"Failed to load image file: {image_path} ({exc})"
        ) from exc


def validate_class_name(class_name: str) -> str:
    """
    Ensure ``class_name`` exists in the canonical class mapping.

    Raises:
        InvalidClassLabelError: If the label is unknown.
    """
    if class_name not in CLASS_TO_IDX:
        raise InvalidClassLabelError(
            f"Invalid class label '{class_name}'. "
            f"Expected one of: {list(DEFECT_CLASSES)}"
        )
    return class_name


# ---------------------------------------------------------------------------
# Transforms (identical resize / normalize for train and inference)
# ---------------------------------------------------------------------------


def get_train_transforms() -> transforms.Compose:
    """
    Build the training transform pipeline.

    Includes light augmentation that preserves wafer defect patterns, then
    the shared resize → tensor → ImageNet normalize steps.
    """
    return transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.RandomHorizontalFlip(p=AUG_HORIZONTAL_FLIP_PROB),
            transforms.RandomRotation(degrees=AUG_ROTATION_DEGREES),
            transforms.RandomAffine(
                degrees=0,
                translate=AUG_TRANSLATE,
                scale=AUG_SCALE,
            ),
            transforms.ColorJitter(
                brightness=AUG_BRIGHTNESS,
                contrast=AUG_CONTRAST,
                saturation=AUG_SATURATION,
            ),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def get_eval_transforms() -> transforms.Compose:
    """
    Build the evaluation / prediction / Grad-CAM transform pipeline.

    No augmentation — only resize, tensor conversion, and ImageNet
    normalization so inference matches training resolution and stats.
    """
    return transforms.Compose(
        [
            transforms.Resize((IMG_SIZE, IMG_SIZE)),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


def resize_rgb_to_img_size(
    image: Image.Image | Path | str | np.ndarray,
) -> np.ndarray:
    """
    Canonical 224×224 uint8 RGB used by die analysis, overlays, density, and Grad-CAM.

    Uses the same bilinear resize as evaluation transforms so all panels share
    one pixel lattice (prevents overlay/density markers drifting vs original/CAM).
    """
    if isinstance(image, np.ndarray):
        array = image
        if array.ndim == 2:
            array = np.stack([array, array, array], axis=-1)
        if array.ndim != 3 or array.shape[2] < 3:
            raise PreprocessError(f"Expected RGB array; got shape={getattr(image, 'shape', None)}")
        array = array[:, :, :3]
        if array.dtype != np.uint8:
            array = np.clip(array, 0, 255).astype(np.uint8)
        pil = Image.fromarray(array, mode="RGB")
    elif isinstance(image, Image.Image):
        pil = image.convert("RGB")
    elif isinstance(image, (str, Path)):
        pil = load_image(image)
    else:
        raise PreprocessError(f"Unsupported image type for resize: {type(image)!r}")

    if pil.size != (IMG_SIZE, IMG_SIZE):
        # Match torchvision Resize default (bilinear) used by preprocess_image / Grad-CAM.
        pil = pil.resize((IMG_SIZE, IMG_SIZE), Image.Resampling.BILINEAR)
    return np.ascontiguousarray(np.asarray(pil, dtype=np.uint8))


def get_inference_transforms() -> transforms.Compose:
    """Alias for :func:`get_eval_transforms` (prediction / Grad-CAM)."""
    return get_eval_transforms()


# ---------------------------------------------------------------------------
# Single-image preprocessing
# ---------------------------------------------------------------------------


def preprocess_image(
    image: Image.Image | Path | str | np.ndarray,
    *,
    augment: bool = False,
) -> Tensor:
    """
    Preprocess a single wafer image into a model-ready tensor.

    Pipeline: load (if needed) → RGB → resize 224×224 → tensor → normalize.

    Args:
        image: PIL image, filesystem path, or RGB ``numpy`` array (H, W, 3).
        augment: If True, apply training augmentation. Must be False for
            evaluation, prediction, and Grad-CAM.

    Returns:
        Float tensor of shape ``(3, IMG_SIZE, IMG_SIZE)``.
    """
    pil_image = _to_pil_image(image)
    transform = get_train_transforms() if augment else get_eval_transforms()
    tensor = transform(pil_image)
    if not isinstance(tensor, Tensor):
        raise PreprocessError("Transform pipeline did not return a Tensor.")
    return tensor


def preprocess_image_batch(
    images: Sequence[Image.Image | Path | str | np.ndarray],
    *,
    augment: bool = False,
) -> Tensor:
    """
    Preprocess multiple images and stack them into a batch tensor.

    Returns:
        Float tensor of shape ``(N, 3, IMG_SIZE, IMG_SIZE)``.
    """
    if not images:
        raise PreprocessError("Cannot preprocess an empty image sequence.")
    tensors = [preprocess_image(image, augment=augment) for image in images]
    import torch

    return torch.stack(tensors, dim=0)


def _to_pil_image(image: Image.Image | Path | str | np.ndarray) -> Image.Image:
    """Convert supported inputs to an RGB PIL image."""
    if isinstance(image, Image.Image):
        return image.convert("RGB")
    if isinstance(image, (str, Path)):
        return load_image(image)
    if isinstance(image, np.ndarray):
        if image.ndim != 3 or image.shape[2] != 3:
            raise PreprocessError(
                f"Expected RGB array with shape (H, W, 3); got {image.shape}."
            )
        array = image
        if array.dtype != np.uint8:
            if np.issubdtype(array.dtype, np.floating):
                max_value = float(array.max()) if array.size else 1.0
                if max_value <= 1.0:
                    array = (np.clip(array, 0.0, 1.0) * 255.0).astype(np.uint8)
                else:
                    array = np.clip(array, 0.0, 255.0).astype(np.uint8)
            else:
                array = np.clip(array, 0, 255).astype(np.uint8)
        return Image.fromarray(array, mode="RGB")
    raise PreprocessError(
        f"Unsupported image type: {type(image)!r}. "
        "Expected PIL.Image, path, or numpy ndarray."
    )


# ---------------------------------------------------------------------------
# Wafer mask
# ---------------------------------------------------------------------------


def create_wafer_mask(
    size: int = IMG_SIZE,
    *,
    center_x: float | None = None,
    center_y: float | None = None,
    radius: float | None = None,
) -> np.ndarray:
    """
    Create a circular wafer mask of shape ``(size, size)``.

    Pixels inside the wafer circle are ``1.0``; pixels outside are ``0.0``
    (black). Geometry defaults to the constants in ``wafer_constants``.

    Args:
        size: Square mask edge length (default ``IMG_SIZE``).
        center_x: Circle center X. Defaults to ``CENTER_X`` scaled to size.
        center_y: Circle center Y. Defaults to ``CENTER_Y`` scaled to size.
        radius: Circle radius. Defaults to ``WAFER_RADIUS`` scaled to size.

    Returns:
        Float32 array of shape ``(size, size)`` with values in ``{0.0, 1.0}``.
    """
    if size <= 0:
        raise PreprocessError(f"Mask size must be positive; got {size}.")

    scale = size / float(IMG_SIZE)
    cx = CENTER_X * scale if center_x is None else float(center_x)
    cy = CENTER_Y * scale if center_y is None else float(center_y)
    rad = WAFER_RADIUS * scale if radius is None else float(radius)

    yy, xx = np.ogrid[:size, :size]
    distance = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    mask = (distance <= rad).astype(np.float32)
    return mask


def apply_wafer_mask(
    image: np.ndarray | Tensor,
    mask: np.ndarray | None = None,
) -> np.ndarray | Tensor:
    """
    Apply a circular wafer mask, zeroing pixels outside the wafer.

    Accepts:
        - ``numpy`` arrays shaped ``(H, W)``, ``(H, W, C)``, or ``(C, H, W)``
        - ``torch`` tensors with the same layouts

    Returns a masked copy of the same type as ``image``.
    """
    if mask is None:
        if isinstance(image, Tensor):
            height, width = int(image.shape[-2]), int(image.shape[-1])
        else:
            if image.ndim == 3 and image.shape[0] in (1, 3) and image.shape[-1] not in (1, 3):
                height, width = int(image.shape[1]), int(image.shape[2])
            else:
                height, width = int(image.shape[0]), int(image.shape[1])
        if height != width:
            raise PreprocessError(
                f"Wafer mask requires a square image; got {height}x{width}."
            )
        mask = create_wafer_mask(size=height)

    if isinstance(image, Tensor):
        import torch

        mask_tensor = torch.as_tensor(mask, dtype=image.dtype, device=image.device)
        if image.ndim == 2:
            return image * mask_tensor
        if image.ndim == 3:
            # (C, H, W) deep-learning layout
            if image.shape[0] in (1, 3) and image.shape[1] == mask.shape[0]:
                return image * mask_tensor.unsqueeze(0)
            # (H, W, C) layout
            if image.shape[2] in (1, 3) and image.shape[0] == mask.shape[0]:
                return image * mask_tensor.unsqueeze(-1)
        raise PreprocessError(
            f"Unsupported tensor shape for masking: {tuple(image.shape)}"
        )

    if not isinstance(image, np.ndarray):
        raise PreprocessError(
            f"Unsupported image type for masking: {type(image)!r}"
        )

    if image.ndim == 2:
        return image * mask
    if image.ndim == 3:
        if image.shape[0] in (1, 3) and image.shape[1] == mask.shape[0]:
            return image * mask[np.newaxis, :, :]
        if image.shape[2] in (1, 3) and image.shape[0] == mask.shape[0]:
            return image * mask[:, :, np.newaxis]
    raise PreprocessError(
        f"Unsupported array shape for masking: {image.shape}"
    )


# ---------------------------------------------------------------------------
# Dataset discovery
# ---------------------------------------------------------------------------


def _iter_image_files(directory: Path) -> Iterator[Path]:
    """Yield supported image files in ``directory`` (non-recursive)."""
    for path in sorted(directory.iterdir()):
        if path.is_file() and is_supported_image(path):
            yield path


def discover_split_samples(
    split_dir: Path | str,
    *,
    class_names: Sequence[str] = DEFECT_CLASSES,
) -> list[tuple[Path, int, str]]:
    """
    Discover ``(image_path, class_index, filename)`` samples under a split.

    Expects ImageFolder layout: ``split_dir/<ClassName>/*.jpg|png|bmp``.

    Raises:
        MissingFileError: If the split directory does not exist.
        InvalidClassLabelError: If an unexpected class folder is present.
        EmptyDirectoryError: If no valid images are found.
    """
    root = Path(split_dir)
    if not root.is_dir():
        raise MissingFileError(f"Dataset split directory not found: {root}")

    allowed = set(class_names)
    samples: list[tuple[Path, int, str]] = []

    class_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if not class_dirs:
        raise EmptyDirectoryError(f"No class directories found in: {root}")

    for class_dir in class_dirs:
        class_name = class_dir.name
        if class_name not in allowed:
            raise InvalidClassLabelError(
                f"Unexpected class folder '{class_name}' in {root}. "
                f"Expected exactly: {list(class_names)}"
            )
        validate_class_name(class_name)
        class_index = CLASS_TO_IDX[class_name]

        image_files = list(_iter_image_files(class_dir))
        if not image_files:
            raise EmptyDirectoryError(
                f"No supported images found in class directory: {class_dir}"
            )

        for image_path in image_files:
            samples.append((image_path, class_index, image_path.name))

    # Ensure every required class folder exists
    found_classes = {path.name for path in class_dirs}
    missing = [name for name in class_names if name not in found_classes]
    if missing:
        raise MissingFileError(
            f"Missing required class folders in {root}: {missing}"
        )

    if not samples:
        raise EmptyDirectoryError(f"No images discovered in split: {root}")

    logger.info("Discovered %d samples in %s", len(samples), root)
    return samples


def resolve_split_directory(split: str) -> Path:
    """
    Map a split name to its configured directory.

    Supported splits: ``train``, ``valid`` / ``val``, ``test``.
    """
    normalized = split.strip().lower()
    mapping = {
        "train": TRAIN_DIR,
        "valid": VALID_DIR,
        "val": VALID_DIR,
        "validation": VALID_DIR,
        "test": TEST_DIR,
    }
    if normalized not in mapping:
        raise PreprocessError(
            f"Unknown dataset split '{split}'. "
            f"Expected one of: {sorted(set(mapping))}"
        )
    return mapping[normalized]


# ---------------------------------------------------------------------------
# PyTorch Dataset
# ---------------------------------------------------------------------------


class WaferDataset(Dataset):
    """
    PyTorch Dataset for wafer defect classification.

    Reads an ImageFolder-style split, applies transforms, and returns
    ``(image_tensor, class_index, filename)``. Performs no model inference.
    """

    def __init__(
        self,
        split_dir: Path | str,
        transform: Callable[[Image.Image], Tensor] | None = None,
        *,
        class_names: Sequence[str] = DEFECT_CLASSES,
    ) -> None:
        self.split_dir = Path(split_dir)
        self.transform = transform or get_eval_transforms()
        self.class_names = tuple(class_names)
        self.samples = discover_split_samples(
            self.split_dir, class_names=self.class_names
        )
        self.class_to_idx = {
            name: CLASS_TO_IDX[name] for name in self.class_names
        }
        self.idx_to_class = {
            index: name for name, index in self.class_to_idx.items()
        }

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> tuple[Tensor, int, str]:
        if index < 0 or index >= len(self.samples):
            raise IndexError(
                f"Dataset index {index} out of range "
                f"[0, {len(self.samples)})."
            )

        image_path, class_index, filename = self.samples[index]
        image = load_image(image_path)
        tensor = self.transform(image)
        if not isinstance(tensor, Tensor):
            raise PreprocessError(
                f"Transform for {image_path} did not return a Tensor."
            )
        return tensor, class_index, filename

    @property
    def labels(self) -> list[int]:
        """Return the list of class indices for all samples."""
        return [class_index for _, class_index, _ in self.samples]

    @property
    def filenames(self) -> list[str]:
        """Return the list of filenames for all samples."""
        return [filename for _, _, filename in self.samples]


# ---------------------------------------------------------------------------
# DataLoader factories
# ---------------------------------------------------------------------------


def create_dataset(
    split: str,
    *,
    augment: bool | None = None,
    transform: Callable[[Image.Image], Tensor] | None = None,
) -> WaferDataset:
    """
    Create a :class:`WaferDataset` for ``train``, ``valid``, or ``test``.

    If ``transform`` is omitted:
        - ``train`` uses augmentation when ``augment`` is True or None
        - ``valid`` / ``test`` never use augmentation
    """
    split_dir = resolve_split_directory(split)
    normalized = split.strip().lower()

    if transform is not None:
        selected_transform = transform
    else:
        use_augment = (
            bool(augment)
            if augment is not None
            else normalized == "train"
        )
        if normalized != "train":
            use_augment = False
        selected_transform = (
            get_train_transforms() if use_augment else get_eval_transforms()
        )

    return WaferDataset(split_dir, transform=selected_transform)


def create_dataloader(
    split: str,
    *,
    batch_size: int = DEFAULT_BATCH_SIZE,
    shuffle: bool | None = None,
    num_workers: int = DEFAULT_NUM_WORKERS,
    pin_memory: bool = DEFAULT_PIN_MEMORY,
    augment: bool | None = None,
    drop_last: bool = False,
) -> DataLoader:
    """
    Create a reusable DataLoader for a dataset split.

    Defaults:
        - ``train`` → shuffle enabled, augmentation enabled
        - ``valid`` / ``test`` → shuffle disabled, no augmentation
    """
    normalized = split.strip().lower()
    if shuffle is None:
        shuffle = normalized == "train"

    dataset = create_dataset(split, augment=augment)

    import torch

    effective_pin_memory = bool(pin_memory) and torch.cuda.is_available()

    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=effective_pin_memory,
        drop_last=drop_last,
    )


def get_train_loader(
    batch_size: int = DEFAULT_BATCH_SIZE,
    *,
    num_workers: int = DEFAULT_NUM_WORKERS,
    pin_memory: bool = DEFAULT_PIN_MEMORY,
    shuffle: bool = True,
) -> DataLoader:
    """Create the training DataLoader (shuffle + augmentation)."""
    return create_dataloader(
        "train",
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=pin_memory,
        augment=True,
    )


def get_valid_loader(
    batch_size: int = DEFAULT_BATCH_SIZE,
    *,
    num_workers: int = DEFAULT_NUM_WORKERS,
    pin_memory: bool = DEFAULT_PIN_MEMORY,
) -> DataLoader:
    """Create the validation DataLoader (no shuffle, no augmentation)."""
    return create_dataloader(
        "valid",
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        augment=False,
    )


def get_test_loader(
    batch_size: int = DEFAULT_BATCH_SIZE,
    *,
    num_workers: int = DEFAULT_NUM_WORKERS,
    pin_memory: bool = DEFAULT_PIN_MEMORY,
) -> DataLoader:
    """Create the test DataLoader (no shuffle, no augmentation)."""
    return create_dataloader(
        "test",
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=pin_memory,
        augment=False,
    )


def summarize_dataset(split: str) -> dict[str, int | str]:
    """
    Return a lightweight summary of a split without loading images.

    Useful for logging and sanity checks before training.
    """
    samples = discover_split_samples(resolve_split_directory(split))
    counts: dict[str, int] = {name: 0 for name in DEFECT_CLASSES}
    for _, class_index, _ in samples:
        if class_index not in IDX_TO_CLASS:
            raise InvalidClassLabelError(f"Unknown class index: {class_index}")
        counts[IDX_TO_CLASS[class_index]] += 1
    return {
        "split": split,
        "total": len(samples),
        "num_classes": len(DEFECT_CLASSES),
        "root": str(resolve_split_directory(split)),
        **{f"count_{name}": count for name, count in counts.items()},
    }


def assert_dataset_root_ready(root: Path | str = DATASET_ROOT) -> None:
    """
    Verify that the configured dataset root and required splits exist.

    Raises meaningful errors if the local dataset is incomplete.
    """
    dataset_root = Path(root)
    if not dataset_root.is_dir():
        raise MissingFileError(
            f"Dataset root not found: {dataset_root}. "
            "Use only the bundled 'wafer dataset/data/' directory."
        )

    for split_name, split_dir in (
        ("train", TRAIN_DIR),
        ("valid", VALID_DIR),
        ("test", TEST_DIR),
    ):
        if not split_dir.is_dir():
            raise MissingFileError(
                f"Required split '{split_name}' not found at: {split_dir}"
            )
        # Force discovery validation (class folders + at least one image)
        discover_split_samples(split_dir)

    logger.info("Dataset root ready: %s", dataset_root)


__all__ = [
    "PreprocessError",
    "MissingFileError",
    "UnsupportedFormatError",
    "CorruptedImageError",
    "EmptyDirectoryError",
    "InvalidClassLabelError",
    "is_supported_image",
    "validate_image_path",
    "load_image",
    "validate_class_name",
    "get_train_transforms",
    "get_eval_transforms",
    "get_inference_transforms",
    "resize_rgb_to_img_size",
    "preprocess_image",
    "preprocess_image_batch",
    "create_wafer_mask",
    "apply_wafer_mask",
    "discover_split_samples",
    "resolve_split_directory",
    "WaferDataset",
    "create_dataset",
    "create_dataloader",
    "get_train_loader",
    "get_valid_loader",
    "get_test_loader",
    "summarize_dataset",
    "assert_dataset_root_ready",
]
