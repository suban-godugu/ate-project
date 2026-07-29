"""
ResNet50 wafer defect classification model for WaferVision-AI.

Responsibility: model architecture and model-management utilities only.
No training loops, evaluation loops, preprocessing, or API code.

Public API:
    WaferClassifier, load_model, save_model, model_summary
"""

from __future__ import annotations

import logging
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
import torch.nn as nn
from torch import Tensor
from torch.optim import Adam, Optimizer
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torchvision.models import ResNet50_Weights, resnet50

from .config import MODEL_PATH, MODELS_DIR
from .wafer_constants import (
    CLASS_TO_IDX,
    DEFECT_CLASSES,
    IMG_SIZE,
    NUM_CLASSES,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Training-configuration defaults (model utilities only — not domain constants)
# ---------------------------------------------------------------------------
DEFAULT_LEARNING_RATE: float = 1e-4
DEFAULT_WEIGHT_DECAY: float = 1e-4
DEFAULT_EARLY_STOPPING_PATIENCE: int = 10
DEFAULT_SCHEDULER_FACTOR: float = 0.1
DEFAULT_SCHEDULER_PATIENCE: int = 5
DEFAULT_SEED: int = 42
BACKBONE_NAME: str = "resnet50"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ModelError(Exception):
    """Base exception for model architecture / checkpoint failures."""


class MissingModelFileError(ModelError):
    """Raised when a checkpoint path does not exist."""


class CorruptedCheckpointError(ModelError):
    """Raised when a checkpoint cannot be loaded or parsed."""


class InvalidClassCountError(ModelError):
    """Raised when the classifier head does not match NUM_CLASSES."""


class InvalidWeightFileError(ModelError):
    """Raised when model weights are incompatible with WaferClassifier."""


class UnsupportedDeviceError(ModelError):
    """Raised when an explicit device request cannot be satisfied."""


# ---------------------------------------------------------------------------
# Training configuration payload (stored inside checkpoints)
# ---------------------------------------------------------------------------


@dataclass
class TrainingConfig:
    """Serializable training hyperparameters stored with checkpoints."""

    learning_rate: float = DEFAULT_LEARNING_RATE
    weight_decay: float = DEFAULT_WEIGHT_DECAY
    freeze_backbone: bool = True
    unfreeze_layer4: bool = False
    num_classes: int = NUM_CLASSES
    image_size: int = IMG_SIZE
    backbone: str = BACKBONE_NAME
    seed: int = DEFAULT_SEED
    early_stopping_patience: int = DEFAULT_EARLY_STOPPING_PATIENCE
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any] | None) -> "TrainingConfig":
        """Build a config from a checkpoint payload."""
        if not payload:
            return cls()
        known = {
            "learning_rate",
            "weight_decay",
            "freeze_backbone",
            "unfreeze_layer4",
            "num_classes",
            "image_size",
            "backbone",
            "seed",
            "early_stopping_patience",
            "extra",
        }
        filtered = {key: payload[key] for key in known if key in payload}
        return cls(**filtered)


# ---------------------------------------------------------------------------
# Device & reproducibility
# ---------------------------------------------------------------------------


def get_device(prefer_cuda: bool = True) -> torch.device:
    """
    Select CUDA when available, otherwise CPU.

    Raises:
        UnsupportedDeviceError: If ``prefer_cuda`` is True but CUDA is broken.
    """
    if prefer_cuda and torch.cuda.is_available():
        try:
            device = torch.device("cuda")
            # Force a trivial allocation to surface driver issues early.
            torch.empty(1, device=device)
            return device
        except Exception as exc:  # noqa: BLE001 - surface as UnsupportedDeviceError
            raise UnsupportedDeviceError(
                f"CUDA was requested but is unusable: {exc}"
            ) from exc
    return torch.device("cpu")


def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Seed Python, NumPy, and PyTorch for deterministic behaviour."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ---------------------------------------------------------------------------
# WaferClassifier
# ---------------------------------------------------------------------------


class WaferClassifier(nn.Module):
    """
    ResNet50 transfer-learning classifier for 9 wafer defect classes.

    Forward pass returns raw logits (no Softmax). Softmax belongs in
    prediction / evaluation modules only.
    """

    def __init__(
        self,
        num_classes: int = NUM_CLASSES,
        *,
        pretrained: bool = True,
        freeze_backbone: bool = True,
        unfreeze_layer4: bool = False,
    ) -> None:
        super().__init__()
        if num_classes != NUM_CLASSES:
            raise InvalidClassCountError(
                f"Expected exactly {NUM_CLASSES} output classes "
                f"({list(DEFECT_CLASSES)}); got {num_classes}."
            )

        weights = ResNet50_Weights.DEFAULT if pretrained else None
        self.backbone = resnet50(weights=weights)
        in_features = int(self.backbone.fc.in_features)
        self.backbone.fc = nn.Linear(in_features, num_classes)

        self.num_classes = num_classes
        self.backbone_name = BACKBONE_NAME

        if freeze_backbone:
            self.freeze_backbone()
        if unfreeze_layer4:
            self.unfreeze_layer4()

    def forward(self, inputs: Tensor) -> Tensor:
        """Return raw logits of shape ``(N, NUM_CLASSES)``."""
        return self.backbone(inputs)

    def freeze_backbone(self) -> None:
        """Freeze all ResNet50 layers except the final classifier head."""
        for name, parameter in self.backbone.named_parameters():
            parameter.requires_grad = name.startswith("fc.")
        logger.info("Backbone frozen; training classifier head only.")

    def unfreeze_layer4(self) -> None:
        """Optionally unfreeze ResNet ``layer4`` for fine-tuning."""
        for parameter in self.backbone.layer4.parameters():
            parameter.requires_grad = True
        for parameter in self.backbone.fc.parameters():
            parameter.requires_grad = True
        logger.info("ResNet layer4 and classifier head are trainable.")

    def freeze_all(self) -> None:
        """Freeze every parameter (useful for pure inference)."""
        for parameter in self.parameters():
            parameter.requires_grad = False

    def count_parameters(self) -> dict[str, int]:
        """Return total / trainable / frozen parameter counts."""
        total = sum(parameter.numel() for parameter in self.parameters())
        trainable = sum(
            parameter.numel()
            for parameter in self.parameters()
            if parameter.requires_grad
        )
        return {
            "total": int(total),
            "trainable": int(trainable),
            "frozen": int(total - trainable),
        }

    @property
    def classifier(self) -> nn.Module:
        """Expose the final fully-connected head."""
        return self.backbone.fc


def build_model(
    *,
    pretrained: bool = True,
    freeze_backbone: bool = True,
    unfreeze_layer4: bool = False,
    device: torch.device | str | None = None,
) -> WaferClassifier:
    """
    Construct a :class:`WaferClassifier` and move it to ``device``.

    If ``device`` is omitted, CUDA is used when available.
    """
    target = get_device() if device is None else torch.device(device)
    model = WaferClassifier(
        num_classes=NUM_CLASSES,
        pretrained=pretrained,
        freeze_backbone=freeze_backbone,
        unfreeze_layer4=unfreeze_layer4,
    )
    return model.to(target)


# ---------------------------------------------------------------------------
# Loss / optimizer / scheduler factories (no training loop)
# ---------------------------------------------------------------------------


def create_criterion(
    class_weights: Tensor | Sequence[float] | None = None,
    *,
    device: torch.device | str | None = None,
) -> nn.CrossEntropyLoss:
    """
    Create ``CrossEntropyLoss``, optionally with class weights.

    Args:
        class_weights: Optional per-class weights (length ``NUM_CLASSES``).
        device: Device for the weight tensor when provided.
    """
    weight_tensor: Tensor | None = None
    if class_weights is not None:
        weight_tensor = torch.as_tensor(class_weights, dtype=torch.float32)
        if weight_tensor.numel() != NUM_CLASSES:
            raise InvalidClassCountError(
                f"class_weights must have length {NUM_CLASSES}; "
                f"got {weight_tensor.numel()}."
            )
        if device is not None:
            weight_tensor = weight_tensor.to(device)
    return nn.CrossEntropyLoss(weight=weight_tensor)


def create_optimizer(
    model: nn.Module,
    *,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    weight_decay: float = DEFAULT_WEIGHT_DECAY,
) -> Adam:
    """Create an Adam optimizer over trainable parameters only."""
    trainable = [parameter for parameter in model.parameters() if parameter.requires_grad]
    if not trainable:
        raise ModelError("No trainable parameters found for optimizer.")
    return Adam(trainable, lr=learning_rate, weight_decay=weight_decay)


def create_scheduler(
    optimizer: Optimizer,
    *,
    factor: float = DEFAULT_SCHEDULER_FACTOR,
    patience: int = DEFAULT_SCHEDULER_PATIENCE,
) -> ReduceLROnPlateau:
    """Create ``ReduceLROnPlateau`` monitoring validation loss."""
    return ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=factor,
        patience=patience,
    )


# ---------------------------------------------------------------------------
# Early stopping & best-checkpoint helpers
# ---------------------------------------------------------------------------


class EarlyStopping:
    """
    Stop training when validation loss stops improving.

    Returns ``True`` from :meth:`step` when patience is exhausted.
    """

    def __init__(
        self,
        patience: int = DEFAULT_EARLY_STOPPING_PATIENCE,
        *,
        min_delta: float = 0.0,
    ) -> None:
        if patience < 1:
            raise ModelError(f"patience must be >= 1; got {patience}.")
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss: float | None = None
        self.bad_epochs = 0
        self.should_stop = False

    def step(self, val_loss: float) -> bool:
        """Update state with the latest validation loss."""
        if self.best_loss is None or val_loss < (self.best_loss - self.min_delta):
            self.best_loss = float(val_loss)
            self.bad_epochs = 0
            self.should_stop = False
            return False

        self.bad_epochs += 1
        self.should_stop = self.bad_epochs >= self.patience
        return self.should_stop

    def state_dict(self) -> dict[str, Any]:
        """Serialize early-stopping state."""
        return {
            "patience": self.patience,
            "min_delta": self.min_delta,
            "best_loss": self.best_loss,
            "bad_epochs": self.bad_epochs,
            "should_stop": self.should_stop,
        }


class BestModelCheckpoint:
    """
    Persist only the checkpoint with the highest validation accuracy.

    Training loops call :meth:`maybe_save` each epoch; this class decides
    whether the new metrics beat the running best.
    """

    def __init__(self, path: Path | str = MODEL_PATH) -> None:
        self.path = Path(path)
        self.best_accuracy: float = float("-inf")

    def maybe_save(
        self,
        model: WaferClassifier,
        *,
        optimizer: Optimizer | None = None,
        epoch: int,
        val_accuracy: float,
        val_loss: float,
        training_config: TrainingConfig | Mapping[str, Any] | None = None,
    ) -> bool:
        """Save when ``val_accuracy`` improves. Returns True if saved."""
        if val_accuracy <= self.best_accuracy:
            return False
        self.best_accuracy = float(val_accuracy)
        save_model(
            self.path,
            model,
            optimizer=optimizer,
            epoch=epoch,
            val_accuracy=val_accuracy,
            val_loss=val_loss,
            training_config=training_config,
        )
        logger.info(
            "Saved new best checkpoint to %s (val_acc=%.4f, val_loss=%.4f)",
            self.path,
            val_accuracy,
            val_loss,
        )
        return True


# ---------------------------------------------------------------------------
# Checkpoint save / load
# ---------------------------------------------------------------------------


def save_model(
    path: Path | str,
    model: WaferClassifier,
    *,
    optimizer: Optimizer | None = None,
    epoch: int | None = None,
    val_accuracy: float | None = None,
    val_loss: float | None = None,
    training_config: TrainingConfig | Mapping[str, Any] | None = None,
    wafer_trained: bool = False,
) -> Path:
    """
    Save a production checkpoint to ``path``.

    Checkpoint fields:
        model_state_dict, optimizer_state_dict, epoch, val_accuracy,
        val_loss, class_mapping, training_config, wafer_trained
    """
    if not isinstance(model, WaferClassifier):
        raise ModelError("save_model expects a WaferClassifier instance.")
    if model.num_classes != NUM_CLASSES:
        raise InvalidClassCountError(
            f"Refusing to save model with {model.num_classes} classes; "
            f"expected {NUM_CLASSES}."
        )

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(training_config, TrainingConfig):
        config_payload = training_config.to_dict()
    elif training_config is None:
        config_payload = TrainingConfig().to_dict()
    else:
        config_payload = dict(training_config)

    checkpoint: dict[str, Any] = {
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": (
            optimizer.state_dict() if optimizer is not None else None
        ),
        "epoch": epoch,
        "val_accuracy": val_accuracy,
        "val_loss": val_loss,
        "class_mapping": dict(CLASS_TO_IDX),
        "training_config": config_payload,
        "num_classes": NUM_CLASSES,
        "backbone": BACKBONE_NAME,
        "image_size": IMG_SIZE,
        "wafer_trained": bool(wafer_trained),
    }

    torch.save(checkpoint, destination)
    logger.info("Checkpoint written to %s", destination)
    return destination


def _load_checkpoint_file(path: Path) -> Any:
    """Load a checkpoint file with clear error messages."""
    if not path.is_file():
        raise MissingModelFileError(f"Model checkpoint not found: {path}")
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        # PyTorch < 2.0 compatibility (no weights_only argument)
        try:
            return torch.load(path, map_location="cpu")
        except Exception as exc:  # noqa: BLE001
            raise CorruptedCheckpointError(
                f"Failed to load checkpoint: {path} ({exc})"
            ) from exc
    except Exception as exc:  # noqa: BLE001
        raise CorruptedCheckpointError(
            f"Failed to load checkpoint: {path} ({exc})"
        ) from exc


def _extract_state_dict(checkpoint: Any) -> dict[str, Tensor]:
    """Extract a model state dict from varied checkpoint layouts."""
    if isinstance(checkpoint, WaferClassifier):
        return checkpoint.state_dict()
    if isinstance(checkpoint, nn.Module):
        return checkpoint.state_dict()
    if isinstance(checkpoint, Mapping):
        if "model_state_dict" in checkpoint:
            state = checkpoint["model_state_dict"]
        elif "state_dict" in checkpoint:
            state = checkpoint["state_dict"]
        else:
            # Raw state_dict saved directly
            state = checkpoint
        if not isinstance(state, Mapping):
            raise InvalidWeightFileError(
                "Checkpoint does not contain a valid model state dict."
            )
        return dict(state)
    raise InvalidWeightFileError(
        f"Unsupported checkpoint type: {type(checkpoint)!r}"
    )


def _validate_class_mapping(checkpoint: Mapping[str, Any]) -> None:
    """Ensure stored class mapping matches the canonical constants."""
    stored = checkpoint.get("class_mapping")
    if stored is None:
        return
    if dict(stored) != dict(CLASS_TO_IDX):
        raise InvalidClassCountError(
            "Checkpoint class_mapping does not match wafer_constants.CLASS_TO_IDX. "
            f"stored={stored}, expected={dict(CLASS_TO_IDX)}"
        )


def load_model(
    path: Path | str = MODEL_PATH,
    *,
    device: torch.device | str | None = None,
    pretrained_backbone: bool = False,
    freeze_backbone: bool = True,
    eval_mode: bool = True,
) -> WaferClassifier:
    """
    Load a WaferVision checkpoint, move to device, and optionally set eval mode.

    Args:
        path: Checkpoint path (default ``config.MODEL_PATH``).
        device: Target device; auto-detected when omitted.
        pretrained_backbone: Whether to initialize ImageNet weights before
            loading the checkpoint (usually False when loading a trained file).
        freeze_backbone: Freeze backbone after construction.
        eval_mode: If True, call ``model.eval()``.

    Returns:
        Ready-to-use :class:`WaferClassifier`.
    """
    checkpoint_path = Path(path)
    checkpoint = _load_checkpoint_file(checkpoint_path)
    state_dict = _extract_state_dict(checkpoint)

    if isinstance(checkpoint, Mapping):
        stored_classes = checkpoint.get("num_classes")
        if stored_classes is not None and int(stored_classes) != NUM_CLASSES:
            raise InvalidClassCountError(
                f"Checkpoint num_classes={stored_classes}, expected {NUM_CLASSES}."
            )
        _validate_class_mapping(checkpoint)

    target = get_device() if device is None else torch.device(device)
    model = WaferClassifier(
        num_classes=NUM_CLASSES,
        pretrained=pretrained_backbone,
        freeze_backbone=freeze_backbone,
        unfreeze_layer4=False,
    )

    try:
        model.load_state_dict(state_dict, strict=True)
    except RuntimeError as exc:
        raise InvalidWeightFileError(
            f"Checkpoint weights are incompatible with WaferClassifier: {exc}"
        ) from exc

    model = model.to(target)
    if eval_mode:
        model.eval()
    logger.info("Loaded model from %s on device %s", checkpoint_path, target)
    return model


# ---------------------------------------------------------------------------
# Metrics helpers (no evaluation loop)
# ---------------------------------------------------------------------------


def accuracy_from_logits(logits: Tensor, targets: Tensor) -> float:
    """Compute overall accuracy from raw logits and integer targets."""
    if logits.ndim != 2:
        raise ModelError(f"Expected logits shaped (N, C); got {tuple(logits.shape)}")
    predictions = torch.argmax(logits, dim=1)
    correct = (predictions == targets).sum().item()
    total = int(targets.numel())
    return float(correct) / float(total) if total else 0.0


def compute_classification_metrics(
    y_true: np.ndarray | list[int] | Tensor,
    y_pred: np.ndarray | list[int] | Tensor,
    *,
    class_names: tuple[str, ...] = DEFECT_CLASSES,
) -> dict[str, Any]:
    """
    Compute precision, recall, F1, confusion matrix, and per-class accuracy.

    This is a pure metric utility for future ``evaluate.py`` use — it does
    not run the model.
    """
    true_np = _to_numpy_int(y_true)
    pred_np = _to_numpy_int(y_pred)
    if true_np.shape != pred_np.shape:
        raise ModelError(
            f"y_true and y_pred shape mismatch: {true_np.shape} vs {pred_np.shape}"
        )

    num_classes = len(class_names)
    confusion = np.zeros((num_classes, num_classes), dtype=np.int64)
    for truth, pred in zip(true_np.tolist(), pred_np.tolist(), strict=True):
        if truth < 0 or truth >= num_classes or pred < 0 or pred >= num_classes:
            raise InvalidClassCountError(
                f"Label out of range for {num_classes} classes: "
                f"y_true={truth}, y_pred={pred}"
            )
        confusion[truth, pred] += 1

    per_class_precision: dict[str, float] = {}
    per_class_recall: dict[str, float] = {}
    per_class_f1: dict[str, float] = {}
    per_class_accuracy: dict[str, float] = {}

    for index, name in enumerate(class_names):
        tp = float(confusion[index, index])
        fp = float(confusion[:, index].sum() - tp)
        fn = float(confusion[index, :].sum() - tp)
        support = float(confusion[index, :].sum())

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            (2.0 * precision * recall / (precision + recall))
            if (precision + recall) > 0
            else 0.0
        )
        class_acc = tp / support if support > 0 else 0.0

        per_class_precision[name] = precision
        per_class_recall[name] = recall
        per_class_f1[name] = f1
        per_class_accuracy[name] = class_acc

    overall_accuracy = (
        float(np.trace(confusion)) / float(confusion.sum())
        if confusion.sum() > 0
        else 0.0
    )

    return {
        "overall_accuracy": overall_accuracy,
        "precision": per_class_precision,
        "recall": per_class_recall,
        "f1": per_class_f1,
        "per_class_accuracy": per_class_accuracy,
        "confusion_matrix": confusion,
        "class_names": list(class_names),
    }


def _to_numpy_int(values: np.ndarray | list[int] | Tensor) -> np.ndarray:
    """Convert labels / predictions to a 1-D int64 NumPy array."""
    if isinstance(values, Tensor):
        array = values.detach().cpu().numpy()
    else:
        array = np.asarray(values)
    return array.astype(np.int64).reshape(-1)


# ---------------------------------------------------------------------------
# Model summary
# ---------------------------------------------------------------------------


def model_summary(
    model: WaferClassifier,
    *,
    device: torch.device | str | None = None,
) -> dict[str, Any]:
    """
    Build and print a concise model summary.

    Returns the summary dictionary for programmatic use.
    """
    if not isinstance(model, WaferClassifier):
        raise ModelError("model_summary expects a WaferClassifier instance.")

    counts = model.count_parameters()
    resolved_device = device
    if resolved_device is None:
        try:
            resolved_device = next(model.parameters()).device
        except StopIteration:
            resolved_device = "unknown"

    summary = {
        "device": str(resolved_device),
        "backbone": model.backbone_name,
        "total_parameters": counts["total"],
        "trainable_parameters": counts["trainable"],
        "frozen_parameters": counts["frozen"],
        "output_classes": model.num_classes,
        "class_names": list(DEFECT_CLASSES),
        "image_size": IMG_SIZE,
    }

    print("WaferVision-AI Model Summary")
    print(f"  Device              : {summary['device']}")
    print(f"  Backbone            : {summary['backbone']}")
    print(f"  Total Parameters    : {summary['total_parameters']:,}")
    print(f"  Trainable Parameters: {summary['trainable_parameters']:,}")
    print(f"  Frozen Parameters   : {summary['frozen_parameters']:,}")
    print(f"  Output Classes      : {summary['output_classes']}")
    return summary


def ensure_models_directory() -> Path:
    """Create ``models/`` if missing and return the path."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR


__all__ = [
    "ModelError",
    "MissingModelFileError",
    "CorruptedCheckpointError",
    "InvalidClassCountError",
    "InvalidWeightFileError",
    "UnsupportedDeviceError",
    "TrainingConfig",
    "WaferClassifier",
    "EarlyStopping",
    "BestModelCheckpoint",
    "get_device",
    "set_seed",
    "build_model",
    "create_criterion",
    "create_optimizer",
    "create_scheduler",
    "save_model",
    "load_model",
    "accuracy_from_logits",
    "compute_classification_metrics",
    "model_summary",
    "ensure_models_directory",
    "DEFAULT_LEARNING_RATE",
    "DEFAULT_WEIGHT_DECAY",
    "DEFAULT_EARLY_STOPPING_PATIENCE",
    "DEFAULT_SEED",
    "BACKBONE_NAME",
]
