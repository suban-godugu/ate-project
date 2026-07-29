"""
Centralized constants for WaferVision-AI.

Holds immutable domain values (class mapping, image size, normalization,
wafer geometry, performance targets). No runtime configuration or business
logic belongs here.

Every module MUST import class mappings and preprocessing constants from
this file. Never duplicate these values elsewhere.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Defect taxonomy — ordering is permanent and must NEVER change
# ---------------------------------------------------------------------------
DEFECT_CLASSES: tuple[str, ...] = (
    "Center",
    "Donut",
    "Edge-Loc",
    "Edge-Ring",
    "Local",
    "Near-Full",
    "Normal",
    "Random",
    "Scratch",
)

NUM_CLASSES: int = len(DEFECT_CLASSES)

# Canonical class mapping (single source of truth)
CLASS_TO_IDX: dict[str, int] = {
    name: index for index, name in enumerate(DEFECT_CLASSES)
}
IDX_TO_CLASS: dict[int, str] = {
    index: name for index, name in enumerate(DEFECT_CLASSES)
}

# ---------------------------------------------------------------------------
# Image geometry — identical for train / eval / predict / Grad-CAM / dies
# ---------------------------------------------------------------------------
IMG_SIZE: int = 224
IMAGE_SIZE: int = IMG_SIZE  # alias kept for Prompt 1 compatibility
IMAGE_CHANNELS: int = 3

# Circular wafer mask geometry (computed once for IMG_SIZE)
CENTER_X: float = IMG_SIZE / 2.0
CENTER_Y: float = IMG_SIZE / 2.0
WAFER_RADIUS: float = IMG_SIZE / 2.0

# ---------------------------------------------------------------------------
# ImageNet normalization — identical for train / eval / predict / Grad-CAM
# ---------------------------------------------------------------------------
IMAGENET_MEAN: tuple[float, float, float] = (0.485, 0.456, 0.406)
IMAGENET_STD: tuple[float, float, float] = (0.229, 0.224, 0.225)

# ---------------------------------------------------------------------------
# Supported image formats
# ---------------------------------------------------------------------------
SUPPORTED_IMAGE_EXTENSIONS: frozenset[str] = frozenset(
    {".jpg", ".jpeg", ".png", ".bmp"}
)

# ---------------------------------------------------------------------------
# Training augmentation parameters (train only — never use at inference)
# ---------------------------------------------------------------------------
AUG_HORIZONTAL_FLIP_PROB: float = 0.5
AUG_ROTATION_DEGREES: float = 10.0
AUG_TRANSLATE: tuple[float, float] = (0.05, 0.05)
AUG_SCALE: tuple[float, float] = (0.95, 1.05)
AUG_BRIGHTNESS: float = 0.10
AUG_CONTRAST: float = 0.10
AUG_SATURATION: float = 0.10

# ---------------------------------------------------------------------------
# DataLoader defaults
# ---------------------------------------------------------------------------
DEFAULT_BATCH_SIZE: int = 32
DEFAULT_NUM_WORKERS: int = 0
DEFAULT_PIN_MEMORY: bool = True

# ---------------------------------------------------------------------------
# Performance targets (milliseconds)
# ---------------------------------------------------------------------------
PREDICTION_TARGET_MS: int = 1000
OVERLAY_TARGET_MS: int = 200
DENSITY_MAP_TARGET_MS: int = 200
CLUSTER_DETECTION_TARGET_MS: int = 100
ZONE_ANALYSIS_TARGET_MS: int = 50
