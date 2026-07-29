"""
Training pipeline for WaferVision-AI.

Responsibility: train the ResNet50 wafer classifier and persist the best
checkpoint (default: ``config.MODEL_PATH`` → ``models/resnet50_layer4_ft.pth``).

CLI examples::

    python -m src.train
    python -m src.train --checkpoint models/resnet50_30epochs.pth

    # Experiment 1 — resume FC-only baseline and fine-tune layer4
    python -m src.train \\
        --resume models/wafer_model.pth \\
        --checkpoint models/resnet50_layer4_ft.pth

Reuses Dataset / DataLoader from ``preprocess.py`` and ``WaferClassifier``
from ``model.py``. Does not redefine preprocessing, class mappings, or the
CNN architecture.
"""

from __future__ import annotations

import argparse
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import torch
from torch import Tensor
from torch.amp import GradScaler, autocast
from torch.nn import CrossEntropyLoss
from torch.optim import Adam, Optimizer
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader

from .config import MODEL_PATH, MODELS_DIR
from .model import (
    BACKBONE_NAME,
    DEFAULT_EARLY_STOPPING_PATIENCE,
    DEFAULT_LEARNING_RATE,
    DEFAULT_SEED,
    DEFAULT_WEIGHT_DECAY,
    EarlyStopping,
    TrainingConfig,
    WaferClassifier,
    build_model,
    compute_classification_metrics,
    create_criterion,
    create_optimizer,
    create_scheduler,
    ensure_models_directory,
    get_device,
    model_summary,
    set_seed,
)
from .preprocess import (
    CorruptedImageError,
    EmptyDirectoryError,
    InvalidClassLabelError,
    MissingFileError,
    PreprocessError,
    assert_dataset_root_ready,
    create_dataloader,
    summarize_dataset,
)
from .wafer_constants import (
    CLASS_TO_IDX,
    DEFAULT_BATCH_SIZE,
    DEFAULT_NUM_WORKERS,
    DEFAULT_PIN_MEMORY,
    DEFECT_CLASSES,
    IMG_SIZE,
    NUM_CLASSES,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class TrainingError(Exception):
    """Base exception for training pipeline failures."""


class CheckpointSaveError(TrainingError):
    """Raised when a checkpoint cannot be written."""


class CudaMemoryTrainingError(TrainingError):
    """Raised when a CUDA out-of-memory error occurs during training."""


# ---------------------------------------------------------------------------
# Configuration (single place)
# ---------------------------------------------------------------------------


@dataclass
class TrainRunConfig:
    """
    Reusable training configuration.

    All training hyperparameters are controlled from this dataclass.
    """

    epochs: int = 30
    batch_size: int = DEFAULT_BATCH_SIZE
    learning_rate: float = DEFAULT_LEARNING_RATE
    weight_decay: float = DEFAULT_WEIGHT_DECAY
    optimizer_name: str = "Adam"
    scheduler_name: str = "ReduceLROnPlateau"
    patience: int = DEFAULT_EARLY_STOPPING_PATIENCE
    scheduler_patience: int = 5
    scheduler_factor: float = 0.1
    checkpoint_path: Path = MODEL_PATH
    seed: int = DEFAULT_SEED
    image_size: int = IMG_SIZE
    num_classes: int = NUM_CLASSES
    num_workers: int = DEFAULT_NUM_WORKERS
    pin_memory: bool = DEFAULT_PIN_MEMORY
    train_split: str = "train"
    val_split: str = "valid"  # keep test held out for evaluate.py
    freeze_backbone: bool = True
    unfreeze_layer4: bool = False
    unfreeze_layer4_after_epoch: int | None = None
    # Experiment 1 — resume + layer4 fine-tune (optional)
    resume_path: Path | None = None
    layer4_learning_rate: float = 1e-5
    fc_learning_rate: float = DEFAULT_LEARNING_RATE
    use_class_weights: bool = False
    use_amp: bool = False
    pretrained: bool = True
    # Dev / smoke knobs (None = full epoch)
    max_train_batches: int | None = None
    max_val_batches: int | None = None
    log_every_n_batches: int = 50
    extra: dict[str, Any] = field(default_factory=dict)

    def to_training_config(self) -> TrainingConfig:
        """Convert to the checkpoint ``TrainingConfig`` payload."""
        return TrainingConfig(
            learning_rate=self.learning_rate,
            weight_decay=self.weight_decay,
            freeze_backbone=self.freeze_backbone,
            unfreeze_layer4=self.unfreeze_layer4,
            num_classes=self.num_classes,
            image_size=self.image_size,
            backbone=BACKBONE_NAME,
            seed=self.seed,
            early_stopping_patience=self.patience,
            extra={
                "epochs": self.epochs,
                "batch_size": self.batch_size,
                "optimizer": self.optimizer_name,
                "scheduler": self.scheduler_name,
                "train_split": self.train_split,
                "val_split": self.val_split,
                "use_class_weights": self.use_class_weights,
                "use_amp": self.use_amp,
                "resume_path": str(self.resume_path) if self.resume_path else None,
                "layer4_learning_rate": self.layer4_learning_rate,
                "fc_learning_rate": self.fc_learning_rate,
                **self.extra,
            },
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize configuration for logging / checkpoints."""
        payload = asdict(self)
        payload["checkpoint_path"] = str(self.checkpoint_path)
        payload["resume_path"] = str(self.resume_path) if self.resume_path else None
        return payload


# ---------------------------------------------------------------------------
# Device reporting
# ---------------------------------------------------------------------------


def print_device_info(device: torch.device) -> None:
    """Print device, GPU name, and memory information."""
    print(f"Device: {device}")
    if device.type == "cuda" and torch.cuda.is_available():
        index = device.index if device.index is not None else torch.cuda.current_device()
        props = torch.cuda.get_device_properties(index)
        total_gb = props.total_memory / (1024**3)
        print(f"GPU Name: {torch.cuda.get_device_name(index)}")
        print(f"Memory: {total_gb:.2f} GB")
    else:
        print("GPU Name: N/A")
        print("Memory: system RAM (CPU mode)")


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------


def _move_batch_to_device(
    images: Tensor,
    labels: Tensor,
    device: torch.device,
) -> tuple[Tensor, Tensor]:
    """Move a batch to the target device."""
    non_blocking = device.type == "cuda"
    return (
        images.to(device, non_blocking=non_blocking),
        labels.to(device, non_blocking=non_blocking),
    )


def _current_lr(optimizer: Optimizer) -> float:
    """Return the first param-group learning rate."""
    return float(optimizer.param_groups[0]["lr"])


def _format_lrs(optimizer: Optimizer) -> str:
    """Format all optimizer param-group learning rates for logging."""
    parts: list[str] = []
    for group in optimizer.param_groups:
        name = group.get("name", "group")
        parts.append(f"{name}={float(group['lr']):.6g}")
    return ", ".join(parts)


def create_differential_optimizer(
    model: WaferClassifier,
    *,
    layer4_lr: float,
    fc_lr: float,
    weight_decay: float = DEFAULT_WEIGHT_DECAY,
) -> Adam:
    """
    Create Adam with separate learning rates for ``layer4`` and ``fc``.

    Args:
        model: Classifier with layer4 + fc trainable (other backbone frozen).
        layer4_lr: Learning rate for ResNet ``layer4``.
        fc_lr: Learning rate for the classifier head.
        weight_decay: Shared Adam weight decay.

    Returns:
        Adam optimizer with named parameter groups ``layer4`` and ``fc``.

    Raises:
        TrainingError: If either parameter group is empty.
    """
    layer4_params = [
        parameter
        for name, parameter in model.backbone.named_parameters()
        if name.startswith("layer4.") and parameter.requires_grad
    ]
    fc_params = [
        parameter
        for name, parameter in model.backbone.named_parameters()
        if name.startswith("fc.") and parameter.requires_grad
    ]
    if not layer4_params:
        raise TrainingError("No trainable layer4 parameters found.")
    if not fc_params:
        raise TrainingError("No trainable fc parameters found.")
    return Adam(
        [
            {"params": layer4_params, "lr": layer4_lr, "name": "layer4"},
            {"params": fc_params, "lr": fc_lr, "name": "fc"},
        ],
        weight_decay=weight_decay,
    )


def summarize_layer_trainability(model: WaferClassifier) -> dict[str, Any]:
    """
    Summarize which ResNet blocks are frozen vs trainable.

    Returns:
        Dict with frozen module names, trainable module names, and counts.
    """
    module_trainable: dict[str, bool] = {
        "conv1": any(p.requires_grad for p in model.backbone.conv1.parameters()),
        "bn1": any(p.requires_grad for p in model.backbone.bn1.parameters()),
        "layer1": any(p.requires_grad for p in model.backbone.layer1.parameters()),
        "layer2": any(p.requires_grad for p in model.backbone.layer2.parameters()),
        "layer3": any(p.requires_grad for p in model.backbone.layer3.parameters()),
        "layer4": any(p.requires_grad for p in model.backbone.layer4.parameters()),
        "fc": any(p.requires_grad for p in model.backbone.fc.parameters()),
    }
    frozen = [name for name, trainable in module_trainable.items() if not trainable]
    trainable = [name for name, trainable in module_trainable.items() if trainable]
    counts = model.count_parameters()
    return {
        "modules": module_trainable,
        "frozen": frozen,
        "trainable": trainable,
        "trainable_params": counts["trainable"],
        "total_params": counts["total"],
    }


def log_finetune_setup(
    *,
    resume_path: Path,
    resumed_epoch: int | None,
    trainability: Mapping[str, Any],
    optimizer: Optimizer,
    resume_strategy: str,
) -> None:
    """Print Experiment 1 fine-tuning setup to the console/logs."""
    print("\n=== Experiment 1 Setup ===")
    print(f"Loaded: {resume_path}")
    print(f"Resumed epoch: {resumed_epoch}")
    print(f"Resume strategy: {resume_strategy}")
    print("\nFrozen")
    for name in trainability["frozen"]:
        print(f"  - {name}")
    print("\nTrainable")
    for name in trainability["trainable"]:
        print(f"  - {name}")
    print(f"\nTrainable parameter count: {trainability['trainable_params']}")
    print("\nOptimizer parameter groups / learning rates")
    for group in optimizer.param_groups:
        name = group.get("name", "group")
        n_params = sum(parameter.numel() for parameter in group["params"])
        print(f"  {name}: lr={float(group['lr']):.6g}  params={n_params}")
    print("=" * 28)


def _estimate_class_weights(loader: DataLoader, device: torch.device) -> Tensor:
    """
    Compute inverse-frequency class weights from a training loader.

    Uses dataset labels when available to avoid a full data pass.
    """
    dataset = loader.dataset
    labels: list[int]
    if hasattr(dataset, "labels"):
        labels = list(dataset.labels)  # type: ignore[attr-defined]
    else:
        labels = []
        for batch in loader:
            _, batch_labels, _ = batch
            labels.extend(int(value) for value in batch_labels.tolist())

    counts = np.bincount(np.asarray(labels, dtype=np.int64), minlength=NUM_CLASSES)
    counts = np.maximum(counts, 1)
    weights = counts.sum() / (NUM_CLASSES * counts.astype(np.float64))
    return torch.tensor(weights, dtype=torch.float32, device=device)


def _build_loaders(config: TrainRunConfig) -> tuple[DataLoader, DataLoader]:
    """Create train and validation dataloaders via preprocess helpers."""
    try:
        assert_dataset_root_ready()
        train_loader = create_dataloader(
            config.train_split,
            batch_size=config.batch_size,
            shuffle=True,
            num_workers=config.num_workers,
            pin_memory=config.pin_memory,
            augment=True,
        )
        val_loader = create_dataloader(
            config.val_split,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=config.num_workers,
            pin_memory=config.pin_memory,
            augment=False,
        )
    except (
        MissingFileError,
        EmptyDirectoryError,
        InvalidClassLabelError,
        PreprocessError,
    ) as exc:
        raise TrainingError(f"Dataset preparation failed: {exc}") from exc

    if len(train_loader.dataset) == 0:  # type: ignore[arg-type]
        raise TrainingError("Training dataset is empty.")
    if len(val_loader.dataset) == 0:  # type: ignore[arg-type]
        raise TrainingError("Validation dataset is empty.")

    return train_loader, val_loader


# ---------------------------------------------------------------------------
# Checkpoint helpers (compatible with model.load_model)
# ---------------------------------------------------------------------------


def save_checkpoint(
    path: Path | str,
    model: WaferClassifier,
    *,
    optimizer: Optimizer | None = None,
    scheduler: ReduceLROnPlateau | None = None,
    epoch: int | None = None,
    train_accuracy: float | None = None,
    val_accuracy: float | None = None,
    val_loss: float | None = None,
    learning_rate: float | None = None,
    training_config: TrainingConfig | Mapping[str, Any] | TrainRunConfig | None = None,
) -> Path:
    """
    Save a production checkpoint compatible with ``model.load_model``.

    Includes model/optimizer/scheduler state, metrics, class mapping, and configuration.
    """
    if not isinstance(model, WaferClassifier):
        raise TrainingError("save_checkpoint expects a WaferClassifier instance.")

    destination = Path(path)
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(training_config, TrainRunConfig):
            config_payload = training_config.to_training_config().to_dict()
        elif isinstance(training_config, TrainingConfig):
            config_payload = training_config.to_dict()
        elif training_config is None:
            config_payload = TrainingConfig().to_dict()
        else:
            config_payload = dict(training_config)

        # Persist train metrics / LR inside training_config.extra as well
        extra = dict(config_payload.get("extra") or {})
        if train_accuracy is not None:
            extra["train_accuracy"] = float(train_accuracy)
        if learning_rate is not None:
            extra["learning_rate_runtime"] = float(learning_rate)
        config_payload["extra"] = extra

        checkpoint: dict[str, Any] = {
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": (
                optimizer.state_dict() if optimizer is not None else None
            ),
            "scheduler_state_dict": (
                scheduler.state_dict() if scheduler is not None else None
            ),
            "epoch": epoch,
            "train_accuracy": train_accuracy,
            "val_accuracy": val_accuracy,
            "val_loss": val_loss,
            "learning_rate": learning_rate,
            "class_mapping": dict(CLASS_TO_IDX),
            "training_config": config_payload,
            "configuration": (
                training_config.to_dict()
                if isinstance(training_config, TrainRunConfig)
                else config_payload
            ),
            "num_classes": NUM_CLASSES,
            "backbone": BACKBONE_NAME,
            "image_size": IMG_SIZE,
        }
        torch.save(checkpoint, destination)
    except OSError as exc:
        raise CheckpointSaveError(
            f"Failed to save checkpoint to {destination}: {exc}"
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise CheckpointSaveError(
            f"Unexpected error while saving checkpoint to {destination}: {exc}"
        ) from exc

    logger.info("Checkpoint saved to %s", destination)
    return destination


def load_checkpoint(
    path: Path | str,
    model: WaferClassifier,
    *,
    optimizer: Optimizer | None = None,
    device: torch.device | str | None = None,
) -> dict[str, Any]:
    """
    Load a checkpoint into ``model`` (and optionally ``optimizer``).

    Returns checkpoint metadata for resume / reporting.
    """
    checkpoint_path = Path(path)
    if not checkpoint_path.is_file():
        raise TrainingError(f"Checkpoint not found: {checkpoint_path}")

    target = get_device() if device is None else torch.device(device)
    try:
        try:
            checkpoint = torch.load(
                checkpoint_path, map_location=target, weights_only=False
            )
        except TypeError:
            checkpoint = torch.load(checkpoint_path, map_location=target)
    except Exception as exc:  # noqa: BLE001
        raise TrainingError(
            f"Failed to load checkpoint {checkpoint_path}: {exc}"
        ) from exc

    if not isinstance(checkpoint, Mapping):
        raise TrainingError(f"Invalid checkpoint format: {checkpoint_path}")

    state = checkpoint.get("model_state_dict") or checkpoint.get("state_dict")
    if state is None:
        raise TrainingError(
            f"Checkpoint missing model_state_dict: {checkpoint_path}"
        )

    stored_mapping = checkpoint.get("class_mapping")
    if stored_mapping is not None and dict(stored_mapping) != dict(CLASS_TO_IDX):
        raise TrainingError(
            "Checkpoint class_mapping does not match wafer_constants.CLASS_TO_IDX."
        )

    try:
        model.load_state_dict(state, strict=True)
    except RuntimeError as exc:
        raise TrainingError(
            f"Incompatible checkpoint weights in {checkpoint_path}: {exc}"
        ) from exc

    model.to(target)

    if optimizer is not None and checkpoint.get("optimizer_state_dict") is not None:
        try:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        except Exception as exc:  # noqa: BLE001
            raise TrainingError(
                f"Failed to restore optimizer state from {checkpoint_path}: {exc}"
            ) from exc

    metadata = {
        "epoch": checkpoint.get("epoch"),
        "train_accuracy": checkpoint.get("train_accuracy"),
        "val_accuracy": checkpoint.get("val_accuracy"),
        "val_loss": checkpoint.get("val_loss"),
        "learning_rate": checkpoint.get("learning_rate"),
        "class_mapping": checkpoint.get("class_mapping", dict(CLASS_TO_IDX)),
        "training_config": checkpoint.get("training_config"),
        "path": str(checkpoint_path),
        "has_optimizer_state": checkpoint.get("optimizer_state_dict") is not None,
        "has_scheduler_state": checkpoint.get("scheduler_state_dict") is not None,
        "optimizer_state_dict": checkpoint.get("optimizer_state_dict"),
        "scheduler_state_dict": checkpoint.get("scheduler_state_dict"),
    }
    logger.info("Loaded checkpoint from %s", checkpoint_path)
    return metadata


# ---------------------------------------------------------------------------
# One-epoch train / validate
# ---------------------------------------------------------------------------


def train_one_epoch(
    model: WaferClassifier,
    loader: DataLoader,
    criterion: CrossEntropyLoss,
    optimizer: Optimizer,
    device: torch.device,
    *,
    use_amp: bool = False,
    max_batches: int | None = None,
    log_every_n_batches: int = 50,
) -> dict[str, float]:
    """
    Run a single training epoch.

    Returns:
        Dictionary with ``loss`` and ``accuracy``.
    """
    model.train()
    running_loss = 0.0
    running_correct = 0
    running_total = 0
    amp_enabled = bool(use_amp and device.type == "cuda")
    scaler = GradScaler("cuda", enabled=amp_enabled)

    for batch_index, batch in enumerate(loader):
        if max_batches is not None and batch_index >= max_batches:
            break

        try:
            images, labels, _filenames = batch
            images, labels = _move_batch_to_device(images, labels, device)
        except CorruptedImageError as exc:
            raise TrainingError(f"Corrupted image during training: {exc}") from exc

        optimizer.zero_grad(set_to_none=True)

        try:
            with autocast(device_type=device.type, enabled=amp_enabled):
                logits = model(images)
                loss = criterion(logits, labels)

            if amp_enabled:
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:
                loss.backward()
                optimizer.step()
        except torch.cuda.OutOfMemoryError as exc:
            torch.cuda.empty_cache()
            raise CudaMemoryTrainingError(
                "CUDA out of memory during training. "
                "Reduce batch_size or disable AMP."
            ) from exc

        batch_size = int(labels.size(0))
        running_loss += float(loss.item()) * batch_size
        predictions = torch.argmax(logits.detach(), dim=1)
        running_correct += int((predictions == labels).sum().item())
        running_total += batch_size

        if log_every_n_batches > 0 and (batch_index + 1) % log_every_n_batches == 0:
            logger.info(
                "  train batch %d — loss=%.4f running_acc=%.4f",
                batch_index + 1,
                running_loss / max(running_total, 1),
                running_correct / max(running_total, 1),
            )

    if running_total == 0:
        raise TrainingError("Training epoch processed zero samples.")

    return {
        "loss": running_loss / running_total,
        "accuracy": running_correct / running_total,
    }


def validate_one_epoch(
    model: WaferClassifier,
    loader: DataLoader,
    criterion: CrossEntropyLoss,
    device: torch.device,
    *,
    use_amp: bool = False,
    max_batches: int | None = None,
    collect_predictions: bool = False,
) -> dict[str, Any]:
    """
    Run a single validation epoch.

    Returns:
        Dictionary with ``loss``, ``accuracy``, and optionally prediction arrays.
    """
    model.eval()
    running_loss = 0.0
    running_correct = 0
    running_total = 0
    all_true: list[int] = []
    all_pred: list[int] = []
    misclassified: list[dict[str, Any]] = []
    amp_enabled = bool(use_amp and device.type == "cuda")

    with torch.no_grad():
        for batch_index, batch in enumerate(loader):
            if max_batches is not None and batch_index >= max_batches:
                break

            try:
                images, labels, filenames = batch
                images, labels = _move_batch_to_device(images, labels, device)
            except CorruptedImageError as exc:
                raise TrainingError(
                    f"Corrupted image during validation: {exc}"
                ) from exc

            try:
                with autocast(device_type=device.type, enabled=amp_enabled):
                    logits = model(images)
                    loss = criterion(logits, labels)
            except torch.cuda.OutOfMemoryError as exc:
                torch.cuda.empty_cache()
                raise CudaMemoryTrainingError(
                    "CUDA out of memory during validation. Reduce batch_size."
                ) from exc

            batch_size = int(labels.size(0))
            running_loss += float(loss.item()) * batch_size
            predictions = torch.argmax(logits, dim=1)
            running_correct += int((predictions == labels).sum().item())
            running_total += batch_size

            if collect_predictions:
                true_list = [int(value) for value in labels.detach().cpu().tolist()]
                pred_list = [
                    int(value) for value in predictions.detach().cpu().tolist()
                ]
                all_true.extend(true_list)
                all_pred.extend(pred_list)
                for truth, pred, filename in zip(
                    true_list, pred_list, list(filenames), strict=True
                ):
                    if truth != pred:
                        misclassified.append(
                            {
                                "filename": filename,
                                "true_label": DEFECT_CLASSES[truth],
                                "predicted_label": DEFECT_CLASSES[pred],
                            }
                        )

    if running_total == 0:
        raise TrainingError("Validation epoch processed zero samples.")

    result: dict[str, Any] = {
        "loss": running_loss / running_total,
        "accuracy": running_correct / running_total,
    }
    if collect_predictions:
        result["y_true"] = all_true
        result["y_pred"] = all_pred
        result["misclassified"] = misclassified
    return result


def validate_model(
    model: WaferClassifier,
    loader: DataLoader,
    criterion: CrossEntropyLoss,
    device: torch.device,
    *,
    use_amp: bool = False,
    max_batches: int | None = None,
) -> dict[str, Any]:
    """
    Full validation pass with precision, recall, F1, and confusion matrix.
    """
    raw = validate_one_epoch(
        model,
        loader,
        criterion,
        device,
        use_amp=use_amp,
        max_batches=max_batches,
        collect_predictions=True,
    )
    metrics = compute_classification_metrics(raw["y_true"], raw["y_pred"])
    return {
        "loss": raw["loss"],
        "accuracy": raw["accuracy"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
        "f1": metrics["f1"],
        "per_class_accuracy": metrics["per_class_accuracy"],
        "overall_accuracy": metrics["overall_accuracy"],
        "confusion_matrix": metrics["confusion_matrix"],
        "misclassified": raw["misclassified"],
        "class_names": metrics["class_names"],
    }


# ---------------------------------------------------------------------------
# Main training orchestration
# ---------------------------------------------------------------------------


def train_model(config: TrainRunConfig | None = None) -> dict[str, Any]:
    """
    Execute the full training pipeline.

    Loads data, builds ``WaferClassifier``, trains with validation, applies
    early stopping, and saves the best checkpoint to ``config.checkpoint_path``.

    When ``config.resume_path`` is set (Experiment 1), restores model weights,
    unfreezes ``layer4`` only, and fine-tunes with differential learning rates.
    In that mode ``config.epochs`` is the number of **additional** fine-tuning
    epochs after the resumed checkpoint epoch (e.g. resume @ 28 with
    ``epochs=30`` trains epochs 29–58).
    """
    config = config or TrainRunConfig()
    if config.num_classes != NUM_CLASSES:
        raise TrainingError(
            f"num_classes must be {NUM_CLASSES}; got {config.num_classes}."
        )
    if config.image_size != IMG_SIZE:
        raise TrainingError(
            f"image_size must remain {IMG_SIZE} for pipeline consistency; "
            f"got {config.image_size}."
        )
    if config.optimizer_name.lower() != "adam":
        raise TrainingError(
            f"Only Adam is supported in this pipeline; got {config.optimizer_name}."
        )

    set_seed(config.seed)
    device = get_device()
    print_device_info(device)
    ensure_models_directory()

    print("\nDataset summary")
    for split_name in (config.train_split, config.val_split):
        summary = summarize_dataset(split_name)
        print(f"  {split_name}: {summary['total']} images, {summary['num_classes']} classes")

    train_loader, val_loader = _build_loaders(config)

    resume_path = Path(config.resume_path) if config.resume_path else None
    if resume_path is not None and resume_path.resolve() == Path(config.checkpoint_path).resolve():
        raise TrainingError(
            "checkpoint_path must differ from resume_path so the baseline is not overwritten."
        )

    # Fresh training starts from ImageNet + config freeze flags.
    # Resume path: load weights with frozen backbone, then enable Experiment 1 layer4 FT.
    if resume_path is not None:
        model = build_model(
            pretrained=config.pretrained,
            freeze_backbone=True,
            unfreeze_layer4=False,
            device=device,
        )
        resume_meta = load_checkpoint(resume_path, model, optimizer=None, device=device)
        print(f"\nCheckpoint successfully loaded: {resume_path}")
        model.unfreeze_layer4()
        config.unfreeze_layer4 = True
        config.freeze_backbone = True  # conv1–layer3 remain frozen via unfreeze_layer4()
        model_summary(model, device=device)

        class_weights = None
        if config.use_class_weights:
            class_weights = _estimate_class_weights(train_loader, device)
            print(f"Using class weights: {class_weights.detach().cpu().tolist()}")

        criterion = create_criterion(class_weights=class_weights, device=device)
        optimizer = create_differential_optimizer(
            model,
            layer4_lr=config.layer4_learning_rate,
            fc_lr=config.fc_learning_rate,
            weight_decay=config.weight_decay,
        )
        scheduler = create_scheduler(
            optimizer,
            factor=config.scheduler_factor,
            patience=config.scheduler_patience,
        )

        # Baseline checkpoints use a single FC param-group Adam. Differential
        # groups are incompatible → recreate optimizer (weights already loaded).
        resume_strategy = (
            "model_weights_restored; optimizer_and_scheduler_recreated "
            "(baseline optimizer was FC-only / single LR; differential "
            "layer4/fc groups require a new Adam state)"
        )
        if resume_meta.get("has_scheduler_state"):
            try:
                scheduler.load_state_dict(resume_meta["scheduler_state_dict"])
                resume_strategy = (
                    "model_weights_restored; optimizer_recreated; "
                    "scheduler_state_restored"
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not restore scheduler state (%s); using fresh scheduler.",
                    exc,
                )

        trainability = summarize_layer_trainability(model)
        for required_frozen in ("conv1", "layer1", "layer2", "layer3"):
            if required_frozen not in trainability["frozen"]:
                raise TrainingError(
                    f"Expected {required_frozen} to remain frozen during layer4 FT."
                )
        for required_train in ("layer4", "fc"):
            if required_train not in trainability["trainable"]:
                raise TrainingError(
                    f"Expected {required_train} to be trainable during layer4 FT."
                )

        resumed_epoch = int(resume_meta.get("epoch") or 0)
        start_epoch = resumed_epoch + 1
        end_epoch = resumed_epoch + config.epochs
        # --resume: config.epochs = number of *additional* fine-tuning epochs
        # e.g. resume @ 28 with epochs=30 → train epochs 29..58 (30 steps)
        log_finetune_setup(
            resume_path=resume_path,
            resumed_epoch=resumed_epoch,
            trainability=trainability,
            optimizer=optimizer,
            resume_strategy=resume_strategy,
        )
        print(
            f"\nFine-tuning schedule: {config.epochs} additional epoch(s) "
            f"(epoch {start_epoch} → {end_epoch}), not capped at the "
            f"original baseline epoch counter."
        )
        best_val_accuracy = float(resume_meta.get("val_accuracy") or float("-inf"))
        best_val_loss = float(resume_meta.get("val_loss") or float("inf"))
        best_epoch = resumed_epoch
        best_train_accuracy = float(resume_meta.get("train_accuracy") or 0.0)
    else:
        model = build_model(
            pretrained=config.pretrained,
            freeze_backbone=config.freeze_backbone,
            unfreeze_layer4=config.unfreeze_layer4,
            device=device,
        )
        model_summary(model, device=device)

        class_weights = None
        if config.use_class_weights:
            class_weights = _estimate_class_weights(train_loader, device)
            print(f"Using class weights: {class_weights.detach().cpu().tolist()}")

        criterion = create_criterion(class_weights=class_weights, device=device)
        optimizer = create_optimizer(
            model,
            learning_rate=config.learning_rate,
            weight_decay=config.weight_decay,
        )
        scheduler = create_scheduler(
            optimizer,
            factor=config.scheduler_factor,
            patience=config.scheduler_patience,
        )
        start_epoch = 1
        end_epoch = config.epochs
        best_val_accuracy = float("-inf")
        best_val_loss = float("inf")
        best_epoch = 0
        best_train_accuracy = 0.0

    early_stopping = EarlyStopping(patience=config.patience)
    history: list[dict[str, float]] = []
    training_config_payload = config.to_training_config()

    print("\nStarting training...")
    start_time = time.perf_counter()

    for epoch in range(start_epoch, end_epoch + 1):
        epoch_start = time.perf_counter()

        # Optional delayed fine-tuning of layer4 (fresh training only)
        if (
            resume_path is None
            and config.unfreeze_layer4_after_epoch is not None
            and epoch == config.unfreeze_layer4_after_epoch
        ):
            print(f"\nUnfreezing ResNet layer4 at epoch {epoch}")
            model.unfreeze_layer4()
            optimizer = create_optimizer(
                model,
                learning_rate=config.learning_rate,
                weight_decay=config.weight_decay,
            )
            scheduler = create_scheduler(
                optimizer,
                factor=config.scheduler_factor,
                patience=config.scheduler_patience,
            )

        try:
            train_stats = train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device,
                use_amp=config.use_amp,
                max_batches=config.max_train_batches,
                log_every_n_batches=config.log_every_n_batches,
            )
            val_stats = validate_one_epoch(
                model,
                val_loader,
                criterion,
                device,
                use_amp=config.use_amp,
                max_batches=config.max_val_batches,
                collect_predictions=False,
            )
        except CudaMemoryTrainingError:
            raise
        except TrainingError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise TrainingError(f"Training failed at epoch {epoch}: {exc}") from exc

        scheduler.step(val_stats["loss"])
        current_lr = _current_lr(optimizer)
        epoch_time = time.perf_counter() - epoch_start

        history.append(
            {
                "epoch": float(epoch),
                "train_loss": train_stats["loss"],
                "train_accuracy": train_stats["accuracy"],
                "val_loss": val_stats["loss"],
                "val_accuracy": val_stats["accuracy"],
                "learning_rate": current_lr,
                "epoch_time_sec": epoch_time,
            }
        )

        print(
            f"Epoch {epoch}/{end_epoch} | "
            f"train_loss={train_stats['loss']:.4f} "
            f"train_acc={train_stats['accuracy']:.4f} | "
            f"val_loss={val_stats['loss']:.4f} "
            f"val_acc={val_stats['accuracy']:.4f} | "
            f"lr=[{_format_lrs(optimizer)}] | "
            f"time={epoch_time:.1f}s"
        )

        improved = val_stats["accuracy"] > best_val_accuracy
        if improved:
            best_val_accuracy = float(val_stats["accuracy"])
            best_val_loss = float(val_stats["loss"])
            best_epoch = epoch
            best_train_accuracy = float(train_stats["accuracy"])
            save_checkpoint(
                config.checkpoint_path,
                model,
                optimizer=optimizer,
                scheduler=scheduler,
                epoch=epoch,
                train_accuracy=train_stats["accuracy"],
                val_accuracy=val_stats["accuracy"],
                val_loss=val_stats["loss"],
                learning_rate=current_lr,
                training_config=config,
            )
            print(
                f"  [saved] best checkpoint -> {config.checkpoint_path} "
                f"(val_acc={best_val_accuracy:.4f})"
            )

        if early_stopping.step(val_stats["loss"]):
            print(
                f"\nEarly stopping triggered at epoch {epoch} "
                f"(patience={config.patience})."
            )
            break

    total_time = time.perf_counter() - start_time

    # Final validation metrics on best weights
    if Path(config.checkpoint_path).is_file():
        load_checkpoint(config.checkpoint_path, model, optimizer=None, device=device)

    final_metrics = validate_model(
        model,
        val_loader,
        criterion,
        device,
        use_amp=config.use_amp,
        max_batches=config.max_val_batches,
    )

    _print_confusion_report(final_metrics)
    _print_training_summary(
        epochs_ran=len(history),
        best_epoch=best_epoch,
        best_accuracy=best_val_accuracy,
        best_val_loss=best_val_loss,
        training_time=total_time,
        model_path=Path(config.checkpoint_path),
        train_accuracy=best_train_accuracy,
    )

    return {
        "history": history,
        "best_epoch": best_epoch,
        "best_val_accuracy": best_val_accuracy,
        "best_val_loss": best_val_loss,
        "best_train_accuracy": best_train_accuracy,
        "training_time_sec": total_time,
        "checkpoint_path": str(config.checkpoint_path),
        "final_metrics": final_metrics,
        "device": str(device),
        "config": config.to_dict(),
        "training_config": training_config_payload.to_dict(),
    }


def _print_confusion_report(metrics: Mapping[str, Any]) -> None:
    """Print confusion matrix, per-class accuracy, and misclassification count."""
    print("\n=== Validation Report (best checkpoint) ===")
    print(f"Overall Accuracy: {metrics['overall_accuracy']:.4f}")
    print("\nPer-Class Accuracy:")
    for name in metrics["class_names"]:
        precision = metrics["precision"][name]
        recall = metrics["recall"][name]
        f1 = metrics["f1"][name]
        acc = metrics["per_class_accuracy"][name]
        print(
            f"  {name:10s}  acc={acc:.4f}  "
            f"precision={precision:.4f}  recall={recall:.4f}  f1={f1:.4f}"
        )

    matrix = metrics["confusion_matrix"]
    print("\nConfusion Matrix (rows=true, cols=pred):")
    header = " ".join(f"{name[:7]:>7s}" for name in metrics["class_names"])
    print(f"{'':10s} {header}")
    for row_index, name in enumerate(metrics["class_names"]):
        row = " ".join(f"{int(matrix[row_index, col]):7d}" for col in range(len(DEFECT_CLASSES)))
        print(f"{name:10s} {row}")

    misclassified = metrics.get("misclassified") or []
    print(f"\nMisclassified samples: {len(misclassified)}")
    for item in misclassified[:20]:
        print(
            f"  {item['filename']}: "
            f"{item['true_label']} -> {item['predicted_label']}"
        )
    if len(misclassified) > 20:
        print(f"  ... and {len(misclassified) - 20} more")


def _print_training_summary(
    *,
    epochs_ran: int,
    best_epoch: int,
    best_accuracy: float,
    best_val_loss: float,
    training_time: float,
    model_path: Path,
    train_accuracy: float,
) -> None:
    """Print the final training summary block."""
    print("\n=== Training Summary ===")
    print(f"Total Epochs        : {epochs_ran}")
    print(f"Best Epoch          : {best_epoch}")
    print(f"Best Val Accuracy   : {best_accuracy:.4f}")
    print(f"Best Val Loss       : {best_val_loss:.4f}")
    print(f"Train Acc @ Best    : {train_accuracy:.4f}")
    print(f"Training Time       : {training_time:.1f}s")
    print(f"Model Saved Path    : {model_path}")


def parse_train_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse training CLI arguments.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Parsed namespace with optional ``checkpoint`` and ``resume`` paths.
    """
    parser = argparse.ArgumentParser(
        description="Train the WaferVision-AI ResNet50 classifier.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help=(
            "Path for the best-model checkpoint save target. "
            f"Default without --resume: {MODEL_PATH}. "
            "Default with --resume: models/resnet50_layer4_ft.pth"
        ),
    )
    parser.add_argument(
        "--resume",
        type=Path,
        default=None,
        help=(
            "Resume from an existing checkpoint and enable Experiment 1 "
            "layer4 fine-tuning (conv1–layer3 frozen; layer4 LR=1e-5, fc LR=1e-4)."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for ``python -m src.train``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    args = parse_train_args(argv)

    resume_path = Path(args.resume) if args.resume else None
    if args.checkpoint is not None:
        checkpoint_path = Path(args.checkpoint)
    elif resume_path is not None:
        checkpoint_path = MODELS_DIR / "resnet50_layer4_ft.pth"
    else:
        checkpoint_path = MODEL_PATH

    config = TrainRunConfig(
        epochs=30,
        batch_size=DEFAULT_BATCH_SIZE,
        learning_rate=DEFAULT_LEARNING_RATE,
        weight_decay=DEFAULT_WEIGHT_DECAY,
        patience=DEFAULT_EARLY_STOPPING_PATIENCE,
        checkpoint_path=checkpoint_path,
        resume_path=resume_path,
        seed=DEFAULT_SEED,
        # Experiment 1 flags are applied inside train_model when resume_path is set
        layer4_learning_rate=1e-5,
        fc_learning_rate=DEFAULT_LEARNING_RATE,
    )
    print("WaferVision-AI Training Pipeline")
    print(f"Checkpoint path: {config.checkpoint_path}")
    if config.resume_path:
        print(f"Resume path    : {config.resume_path}")
    print(f"Models directory: {MODELS_DIR}")
    result = train_model(config)
    print(
        f"\nDone. Best val accuracy={result['best_val_accuracy']:.4f} "
        f"at epoch {result['best_epoch']}."
    )
    return 0


__all__ = [
    "TrainRunConfig",
    "TrainingError",
    "CheckpointSaveError",
    "CudaMemoryTrainingError",
    "print_device_info",
    "train_one_epoch",
    "validate_one_epoch",
    "validate_model",
    "train_model",
    "save_checkpoint",
    "load_checkpoint",
    "create_differential_optimizer",
    "summarize_layer_trainability",
    "parse_train_args",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
