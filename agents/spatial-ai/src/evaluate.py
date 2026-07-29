"""
Evaluation pipeline for WaferVision-AI.

Responsibility: evaluate the trained ResNet50 checkpoint on the test split
and generate production-grade metrics / reports / visualizations.

Reuses ``load_model`` from ``model.py`` and test DataLoaders / transforms from
``preprocess.py``. Does not retrain, redefine the CNN, or duplicate transforms.

Run::

    python -m src.evaluate
"""

from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)
from torch.utils.data import DataLoader

from .config import MODEL_PATH, PROJECT_ROOT
from .model import (
    BACKBONE_NAME,
    MissingModelFileError,
    ModelError,
    WaferClassifier,
    get_device,
    load_model,
)
from .preprocess import (
    CorruptedImageError,
    EmptyDirectoryError,
    InvalidClassLabelError,
    MissingFileError,
    PreprocessError,
    create_dataloader,
    summarize_dataset,
)
from .wafer_constants import (
    CLASS_TO_IDX,
    DEFAULT_BATCH_SIZE,
    DEFAULT_NUM_WORKERS,
    DEFECT_CLASSES,
    IDX_TO_CLASS,
    NUM_CLASSES,
)

logger = logging.getLogger(__name__)

EVALUATION_DIR: Path = PROJECT_ROOT / "evaluation"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class EvaluationError(Exception):
    """Base exception for evaluation pipeline failures."""


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class EvaluateConfig:
    """Runtime configuration for the evaluation pipeline."""

    model_path: Path = MODEL_PATH
    split: str = "test"
    batch_size: int = DEFAULT_BATCH_SIZE
    num_workers: int = DEFAULT_NUM_WORKERS
    output_dir: Path = EVALUATION_DIR
    max_batches: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def ensure_evaluation_directory(output_dir: Path | str = EVALUATION_DIR) -> Path:
    """Create the evaluation output directory if it does not exist."""
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _pct(value: float) -> float:
    """Convert a 0–1 ratio to a percentage with 4 decimal places."""
    return round(float(value) * 100.0, 4)


def _read_checkpoint_metadata(path: Path) -> dict[str, Any]:
    """Read checkpoint metadata without altering ``load_model`` behaviour."""
    if not path.is_file():
        raise EvaluationError(f"Model checkpoint not found: {path}")
    try:
        try:
            checkpoint = torch.load(path, map_location="cpu", weights_only=False)
        except TypeError:
            checkpoint = torch.load(path, map_location="cpu")
    except Exception as exc:  # noqa: BLE001
        raise EvaluationError(f"Failed to read checkpoint metadata: {exc}") from exc

    if not isinstance(checkpoint, Mapping):
        return {"path": str(path)}

    return {
        "path": str(path),
        "epoch": checkpoint.get("epoch"),
        "train_accuracy": checkpoint.get("train_accuracy"),
        "val_accuracy": checkpoint.get("val_accuracy"),
        "val_loss": checkpoint.get("val_loss"),
        "learning_rate": checkpoint.get("learning_rate"),
        "class_mapping": checkpoint.get("class_mapping"),
        "training_config": checkpoint.get("training_config"),
        "num_classes": checkpoint.get("num_classes", NUM_CLASSES),
        "backbone": checkpoint.get("backbone", BACKBONE_NAME),
    }


def _build_test_loader(config: EvaluateConfig) -> DataLoader:
    """Create the test DataLoader using existing preprocess helpers."""
    try:
        loader = create_dataloader(
            config.split,
            batch_size=config.batch_size,
            shuffle=False,
            num_workers=config.num_workers,
            pin_memory=True,
            augment=False,
        )
    except (
        MissingFileError,
        EmptyDirectoryError,
        InvalidClassLabelError,
        PreprocessError,
    ) as exc:
        raise EvaluationError(f"Failed to load evaluation dataset: {exc}") from exc

    if len(loader.dataset) == 0:  # type: ignore[arg-type]
        raise EvaluationError(f"Evaluation dataset '{config.split}' is empty.")
    return loader


# ---------------------------------------------------------------------------
# Prediction over a dataset
# ---------------------------------------------------------------------------


def predict_dataset(
    model: WaferClassifier,
    loader: DataLoader,
    device: torch.device,
    *,
    max_batches: int | None = None,
) -> list[dict[str, Any]]:
    """
    Run inference on every batch and collect per-image predictions.

    Each record contains:
        filename, true_index, true_label, predicted_index, predicted_label,
        confidence, probabilities
    """
    model.eval()
    records: list[dict[str, Any]] = []

    with torch.no_grad():
        for batch_index, batch in enumerate(loader):
            if max_batches is not None and batch_index >= max_batches:
                break

            try:
                images, labels, filenames = batch
            except CorruptedImageError as exc:
                raise EvaluationError(f"Corrupted image during evaluation: {exc}") from exc

            images = images.to(device, non_blocking=device.type == "cuda")
            labels = labels.to(device, non_blocking=device.type == "cuda")

            try:
                logits = model(images)
            except Exception as exc:  # noqa: BLE001
                raise EvaluationError(f"Inference failed: {exc}") from exc

            probabilities = F.softmax(logits, dim=1)
            confidences, predicted = torch.max(probabilities, dim=1)

            for row in range(images.size(0)):
                true_index = int(labels[row].item())
                pred_index = int(predicted[row].item())
                if true_index not in IDX_TO_CLASS or pred_index not in IDX_TO_CLASS:
                    raise EvaluationError(
                        f"Invalid label indices true={true_index} pred={pred_index}."
                    )
                prob_vector = [
                    float(value) for value in probabilities[row].detach().cpu().tolist()
                ]
                records.append(
                    {
                        "filename": filenames[row],
                        "true_index": true_index,
                        "true_label": IDX_TO_CLASS[true_index],
                        "predicted_index": pred_index,
                        "predicted_label": IDX_TO_CLASS[pred_index],
                        "confidence": float(confidences[row].item()),
                        "probabilities": prob_vector,
                        "correct": true_index == pred_index,
                    }
                )

    if not records:
        raise EvaluationError("No predictions were produced (empty evaluation run).")
    return records


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def compute_metrics(predictions: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """
    Compute overall, macro/weighted/micro, per-class, top-k, and confidence metrics.
    """
    if not predictions:
        raise EvaluationError("Cannot compute metrics on an empty prediction list.")

    y_true = np.asarray([row["true_index"] for row in predictions], dtype=np.int64)
    y_pred = np.asarray([row["predicted_index"] for row in predictions], dtype=np.int64)
    confidences = np.asarray([row["confidence"] for row in predictions], dtype=np.float64)
    prob_matrix = np.asarray(
        [row["probabilities"] for row in predictions], dtype=np.float64
    )

    labels = list(range(NUM_CLASSES))
    overall_accuracy = float(accuracy_score(y_true, y_pred))

    precision_macro = float(
        precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    )
    recall_macro = float(
        recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    )
    f1_macro = float(
        f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
    )

    precision_weighted = float(
        precision_score(
            y_true, y_pred, labels=labels, average="weighted", zero_division=0
        )
    )
    recall_weighted = float(
        recall_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
    )
    f1_weighted = float(
        f1_score(y_true, y_pred, labels=labels, average="weighted", zero_division=0)
    )

    precision_micro = float(
        precision_score(y_true, y_pred, labels=labels, average="micro", zero_division=0)
    )
    recall_micro = float(
        recall_score(y_true, y_pred, labels=labels, average="micro", zero_division=0)
    )
    f1_micro = float(
        f1_score(y_true, y_pred, labels=labels, average="micro", zero_division=0)
    )

    per_precision, per_recall, per_f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        average=None,
        zero_division=0,
    )

    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    per_class: list[dict[str, Any]] = []
    for index, class_name in enumerate(DEFECT_CLASSES):
        support_count = int(support[index])
        class_accuracy = (
            float(matrix[index, index]) / float(support_count) if support_count > 0 else 0.0
        )
        false_positives = int(matrix[:, index].sum() - matrix[index, index])
        false_negatives = int(matrix[index, :].sum() - matrix[index, index])
        class_mask = y_true == index
        class_conf = confidences[class_mask]
        per_class.append(
            {
                "class": class_name,
                "precision": float(per_precision[index]),
                "recall": float(per_recall[index]),
                "f1": float(per_f1[index]),
                "accuracy": class_accuracy,
                "support": support_count,
                "false_positives": false_positives,
                "false_negatives": false_negatives,
                "average_confidence": (
                    float(class_conf.mean()) if class_conf.size else 0.0
                ),
            }
        )

    topk = _compute_topk_accuracy(y_true, prob_matrix, ks=(1, 3, 5))

    # Confidence distribution (histogram bins)
    hist_counts, hist_edges = np.histogram(confidences, bins=10, range=(0.0, 1.0))

    correct = int((y_true == y_pred).sum())
    incorrect = int(len(y_true) - correct)

    return {
        "total_images": int(len(y_true)),
        "correct_predictions": correct,
        "incorrect_predictions": incorrect,
        "overall_accuracy": overall_accuracy,
        "precision": {
            "macro": precision_macro,
            "weighted": precision_weighted,
            "micro": precision_micro,
        },
        "recall": {
            "macro": recall_macro,
            "weighted": recall_weighted,
            "micro": recall_micro,
        },
        "f1": {
            "macro": f1_macro,
            "weighted": f1_weighted,
            "micro": f1_micro,
        },
        "per_class": per_class,
        "confusion_matrix": matrix,
        "confidence": {
            "average": float(confidences.mean()) if confidences.size else 0.0,
            "maximum": float(confidences.max()) if confidences.size else 0.0,
            "minimum": float(confidences.min()) if confidences.size else 0.0,
            "distribution_counts": hist_counts.astype(int).tolist(),
            "distribution_edges": hist_edges.astype(float).tolist(),
            "per_class_average": {
                row["class"]: row["average_confidence"] for row in per_class
            },
        },
        "topk_accuracy": topk,
        "y_true": y_true,
        "y_pred": y_pred,
        "confidences": confidences,
    }


def _compute_topk_accuracy(
    y_true: np.ndarray,
    prob_matrix: np.ndarray,
    ks: Sequence[int] = (1, 3, 5),
) -> dict[str, float]:
    """Compute top-k accuracy from softmax probability rows."""
    results: dict[str, float] = {}
    num_classes = prob_matrix.shape[1]
    for k in ks:
        effective_k = min(int(k), num_classes)
        top_indices = np.argpartition(-prob_matrix, effective_k - 1, axis=1)[
            :, :effective_k
        ]
        hits = np.any(top_indices == y_true[:, None], axis=1)
        results[f"top_{k}"] = float(hits.mean()) if hits.size else 0.0
    return results


def generate_confusion_matrix(
    y_true: Sequence[int] | np.ndarray,
    y_pred: Sequence[int] | np.ndarray,
    *,
    class_names: Sequence[str] = DEFECT_CLASSES,
) -> np.ndarray:
    """Generate a ``len(class_names) x len(class_names)`` confusion matrix."""
    labels = list(range(len(class_names)))
    return confusion_matrix(
        np.asarray(y_true, dtype=np.int64),
        np.asarray(y_pred, dtype=np.int64),
        labels=labels,
    )


def generate_classification_report(
    y_true: Sequence[int] | np.ndarray,
    y_pred: Sequence[int] | np.ndarray,
    *,
    class_names: Sequence[str] = DEFECT_CLASSES,
) -> str:
    """Generate a full sklearn classification report string."""
    return classification_report(
        np.asarray(y_true, dtype=np.int64),
        np.asarray(y_pred, dtype=np.int64),
        labels=list(range(len(class_names))),
        target_names=list(class_names),
        digits=4,
        zero_division=0,
    )


# ---------------------------------------------------------------------------
# Misclassified report
# ---------------------------------------------------------------------------


def collect_misclassified(
    predictions: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return misclassified samples sorted by lowest confidence first."""
    rows = [
        {
            "filename": row["filename"],
            "actual_class": row["true_label"],
            "predicted_class": row["predicted_label"],
            "confidence": float(row["confidence"]),
        }
        for row in predictions
        if not row["correct"]
    ]
    rows.sort(key=lambda item: item["confidence"])
    return rows


def save_misclassified_csv(
    misclassified: Sequence[Mapping[str, Any]],
    path: Path | str,
) -> Path:
    """Write misclassified image report to CSV."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["filename", "actual_class", "predicted_class", "confidence"]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in misclassified:
            writer.writerow(
                {
                    "filename": row["filename"],
                    "actual_class": row["actual_class"],
                    "predicted_class": row["predicted_class"],
                    "confidence": f"{float(row['confidence']):.6f}",
                }
            )
    return destination


# ---------------------------------------------------------------------------
# JSON / text reports
# ---------------------------------------------------------------------------


def generate_json_report(
    metrics: Mapping[str, Any],
    *,
    model_name: str,
    checkpoint_meta: Mapping[str, Any] | None = None,
    device: str | None = None,
) -> dict[str, Any]:
    """
    Build the evaluation JSON payload (percentages for headline metrics).
    """
    classes_payload = [
        {
            "class": row["class"],
            "precision": _pct(row["precision"]),
            "recall": _pct(row["recall"]),
            "f1": _pct(row["f1"]),
            "accuracy": _pct(row["accuracy"]),
            "support": int(row["support"]),
            "false_positives": int(row["false_positives"]),
            "false_negatives": int(row["false_negatives"]),
            "average_confidence": _pct(row["average_confidence"]),
        }
        for row in metrics["per_class"]
    ]

    payload: dict[str, Any] = {
        "model": model_name,
        "overall_accuracy": _pct(metrics["overall_accuracy"]),
        "macro_f1": _pct(metrics["f1"]["macro"]),
        "weighted_f1": _pct(metrics["f1"]["weighted"]),
        "micro_f1": _pct(metrics["f1"]["micro"]),
        "macro_precision": _pct(metrics["precision"]["macro"]),
        "weighted_precision": _pct(metrics["precision"]["weighted"]),
        "micro_precision": _pct(metrics["precision"]["micro"]),
        "macro_recall": _pct(metrics["recall"]["macro"]),
        "weighted_recall": _pct(metrics["recall"]["weighted"]),
        "micro_recall": _pct(metrics["recall"]["micro"]),
        "average_confidence": _pct(metrics["confidence"]["average"]),
        "max_confidence": _pct(metrics["confidence"]["maximum"]),
        "min_confidence": _pct(metrics["confidence"]["minimum"]),
        "top1_accuracy": _pct(metrics["topk_accuracy"]["top_1"]),
        "top3_accuracy": _pct(metrics["topk_accuracy"]["top_3"]),
        "top5_accuracy": _pct(metrics["topk_accuracy"]["top_5"]),
        "total_images": metrics["total_images"],
        "correct_predictions": metrics["correct_predictions"],
        "incorrect_predictions": metrics["incorrect_predictions"],
        "classes": classes_payload,
        "class_mapping": dict(CLASS_TO_IDX),
        "device": device,
        "checkpoint": {
            "epoch": None if checkpoint_meta is None else checkpoint_meta.get("epoch"),
            "train_accuracy": (
                None
                if checkpoint_meta is None
                else checkpoint_meta.get("train_accuracy")
            ),
            "val_accuracy": (
                None if checkpoint_meta is None else checkpoint_meta.get("val_accuracy")
            ),
            "backbone": (
                BACKBONE_NAME
                if checkpoint_meta is None
                else checkpoint_meta.get("backbone", BACKBONE_NAME)
            ),
        },
    }
    return payload


def save_json_report(payload: Mapping[str, Any], path: Path | str) -> Path:
    """Write ``evaluation_report.json``."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return destination


def save_classification_report_text(report_text: str, path: Path | str) -> Path:
    """Write ``classification_report.txt``."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(report_text, encoding="utf-8")
    return destination


# ---------------------------------------------------------------------------
# Visualizations
# ---------------------------------------------------------------------------


def save_visualizations(
    metrics: Mapping[str, Any],
    output_dir: Path | str,
) -> dict[str, Path]:
    """
    Save evaluation figures:

    - confusion_matrix.png
    - prediction_distribution.png
    - confidence_histogram.png
    - per_class_accuracy.png
    """
    out = ensure_evaluation_directory(output_dir)
    paths: dict[str, Path] = {}

    matrix = np.asarray(metrics["confusion_matrix"], dtype=np.int64)
    class_names = list(DEFECT_CLASSES)

    # Confusion matrix heatmap
    fig, ax = plt.subplots(figsize=(10, 8))
    image = ax.imshow(matrix, interpolation="nearest", cmap="Blues")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Confusion Matrix")
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right")
    ax.set_yticklabels(class_names)
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            ax.text(
                j,
                i,
                str(int(matrix[i, j])),
                ha="center",
                va="center",
                color="white" if matrix[i, j] > matrix.max() / 2 else "black",
                fontsize=8,
            )
    fig.tight_layout()
    cm_path = out / "confusion_matrix.png"
    fig.savefig(cm_path, dpi=150)
    plt.close(fig)
    paths["confusion_matrix"] = cm_path

    # Prediction distribution
    y_pred = np.asarray(metrics["y_pred"], dtype=np.int64)
    pred_counts = [int(np.sum(y_pred == index)) for index in range(NUM_CLASSES)]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(class_names, pred_counts, color="#2f5d8a")
    ax.set_title("Prediction Distribution")
    ax.set_xlabel("Predicted Class")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    dist_path = out / "prediction_distribution.png"
    fig.savefig(dist_path, dpi=150)
    plt.close(fig)
    paths["prediction_distribution"] = dist_path

    # Confidence histogram
    confidences = np.asarray(metrics["confidences"], dtype=np.float64)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(confidences, bins=20, range=(0.0, 1.0), color="#3d7ea6", edgecolor="white")
    ax.set_title("Confidence Histogram")
    ax.set_xlabel("Confidence")
    ax.set_ylabel("Frequency")
    fig.tight_layout()
    conf_path = out / "confidence_histogram.png"
    fig.savefig(conf_path, dpi=150)
    plt.close(fig)
    paths["confidence_histogram"] = conf_path

    # Per-class accuracy bar chart
    per_class_acc = [float(row["accuracy"]) for row in metrics["per_class"]]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(class_names, per_class_acc, color="#1b7f5a")
    ax.set_ylim(0.0, 1.05)
    ax.set_title("Per-Class Accuracy")
    ax.set_xlabel("Class")
    ax.set_ylabel("Accuracy")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    acc_path = out / "per_class_accuracy.png"
    fig.savefig(acc_path, dpi=150)
    plt.close(fig)
    paths["per_class_accuracy"] = acc_path

    return paths


# ---------------------------------------------------------------------------
# Printing
# ---------------------------------------------------------------------------


def _print_model_summary(
    *,
    device: torch.device,
    model_path: Path,
    checkpoint_meta: Mapping[str, Any],
) -> None:
    """Print model / checkpoint summary."""
    print("\n=== Model Summary ===")
    print(f"Backbone            : {checkpoint_meta.get('backbone', BACKBONE_NAME)}")
    print(f"Number of Classes   : {NUM_CLASSES}")
    print(f"Model Path          : {model_path}")
    print(f"Checkpoint Epoch    : {checkpoint_meta.get('epoch')}")
    print(f"Training Accuracy   : {checkpoint_meta.get('train_accuracy')}")
    print(f"Validation Accuracy : {checkpoint_meta.get('val_accuracy')}")
    print(f"Device              : {device}")


def _print_result_summary(metrics: Mapping[str, Any]) -> None:
    """Print the final evaluation result summary."""
    print("\n=== Result Summary ===")
    print(f"Total Images          : {metrics['total_images']}")
    print(f"Correct Predictions   : {metrics['correct_predictions']}")
    print(f"Incorrect Predictions : {metrics['incorrect_predictions']}")
    print(f"Overall Accuracy      : {_pct(metrics['overall_accuracy']):.2f}%")
    print(f"Macro F1              : {_pct(metrics['f1']['macro']):.2f}%")
    print(f"Weighted F1           : {_pct(metrics['f1']['weighted']):.2f}%")
    print(f"Average Confidence    : {_pct(metrics['confidence']['average']):.2f}%")
    print(f"Top-1 Accuracy        : {_pct(metrics['topk_accuracy']['top_1']):.2f}%")
    print(f"Top-3 Accuracy        : {_pct(metrics['topk_accuracy']['top_3']):.2f}%")
    print(f"Top-5 Accuracy        : {_pct(metrics['topk_accuracy']['top_5']):.2f}%")


def _print_confusion_details(metrics: Mapping[str, Any]) -> None:
    """Print confusion-matrix derived correct / FP / FN details."""
    matrix = np.asarray(metrics["confusion_matrix"], dtype=np.int64)
    print("\n=== Confusion Matrix Details ===")
    print(f"Correct Predictions (trace): {int(np.trace(matrix))}")
    print(f"Misclassifications         : {int(matrix.sum() - np.trace(matrix))}")
    diagonal_acc = (
        float(np.trace(matrix)) / float(matrix.sum()) if matrix.sum() else 0.0
    )
    print(f"Diagonal Accuracy          : {_pct(diagonal_acc):.2f}%")
    for row in metrics["per_class"]:
        print(
            f"  {row['class']:10s} FP={row['false_positives']:4d} "
            f"FN={row['false_negatives']:4d}"
        )


# ---------------------------------------------------------------------------
# Main evaluation orchestration
# ---------------------------------------------------------------------------


def evaluate_model(config: EvaluateConfig | None = None) -> dict[str, Any]:
    """
    Run the full evaluation pipeline on the test set.

    Loads ``config.MODEL_PATH`` (default ``models/resnet50_layer4_ft.pth``),
    evaluates without augmentation, and writes reports / figures under
    ``evaluation/``.
    """
    config = config or EvaluateConfig()
    output_dir = ensure_evaluation_directory(config.output_dir)
    device = get_device()

    print("WaferVision-AI Evaluation Pipeline")
    print(f"Device: {device}")
    print(f"Model : {config.model_path}")
    print(f"Split : {config.split}")

    if not Path(config.model_path).is_file():
        raise EvaluationError(f"Model checkpoint not found: {config.model_path}")

    checkpoint_meta = _read_checkpoint_metadata(Path(config.model_path))
    stored_mapping = checkpoint_meta.get("class_mapping")
    if stored_mapping is not None and dict(stored_mapping) != dict(CLASS_TO_IDX):
        raise EvaluationError(
            "Checkpoint class_mapping does not match wafer_constants.CLASS_TO_IDX."
        )

    try:
        model = load_model(
            config.model_path,
            device=device,
            pretrained_backbone=False,
            freeze_backbone=True,
            eval_mode=True,
        )
    except (MissingModelFileError, ModelError) as exc:
        raise EvaluationError(f"Failed to load model: {exc}") from exc

    _print_model_summary(
        device=device,
        model_path=Path(config.model_path),
        checkpoint_meta=checkpoint_meta,
    )

    try:
        summary = summarize_dataset(config.split)
        print(
            f"\nDataset: {summary['total']} images, "
            f"{summary['num_classes']} classes @ {summary['root']}"
        )
    except PreprocessError as exc:
        raise EvaluationError(f"Dataset summary failed: {exc}") from exc

    loader = _build_test_loader(config)
    predictions = predict_dataset(
        model,
        loader,
        device,
        max_batches=config.max_batches,
    )
    metrics = compute_metrics(predictions)
    report_text = generate_classification_report(metrics["y_true"], metrics["y_pred"])
    matrix = generate_confusion_matrix(metrics["y_true"], metrics["y_pred"])
    metrics["confusion_matrix"] = matrix

    print("\n=== Classification Report ===")
    print(report_text)
    _print_confusion_details(metrics)

    misclassified = collect_misclassified(predictions)
    print(f"\nMisclassified images: {len(misclassified)} (sorted by lowest confidence)")

    json_payload = generate_json_report(
        metrics,
        model_name=Path(config.model_path).name,
        checkpoint_meta=checkpoint_meta,
        device=str(device),
    )

    json_path = save_json_report(json_payload, output_dir / "evaluation_report.json")
    report_path = save_classification_report_text(
        report_text, output_dir / "classification_report.txt"
    )
    csv_path = save_misclassified_csv(
        misclassified, output_dir / "misclassified_images.csv"
    )
    figure_paths = save_visualizations(metrics, output_dir)

    _print_result_summary(metrics)
    print("\n=== Output Files ===")
    print(f"JSON report          : {json_path}")
    print(f"Classification report: {report_path}")
    print(f"Misclassified CSV    : {csv_path}")
    for name, path in figure_paths.items():
        print(f"{name:22s}: {path}")

    return {
        "metrics": metrics,
        "predictions": predictions,
        "misclassified": misclassified,
        "json_report": json_payload,
        "classification_report": report_text,
        "output_files": {
            "evaluation_report_json": str(json_path),
            "classification_report_txt": str(report_path),
            "misclassified_images_csv": str(csv_path),
            **{key: str(value) for key, value in figure_paths.items()},
        },
        "device": str(device),
        "model_path": str(config.model_path),
        "checkpoint": checkpoint_meta,
    }


def main() -> int:
    """CLI entrypoint for ``python -m src.evaluate``."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    result = evaluate_model(EvaluateConfig())
    accuracy = _pct(result["metrics"]["overall_accuracy"])
    print(f"\nDone. Overall test accuracy={accuracy:.2f}%")
    return 0


__all__ = [
    "EVALUATION_DIR",
    "EvaluateConfig",
    "EvaluationError",
    "ensure_evaluation_directory",
    "predict_dataset",
    "compute_metrics",
    "generate_confusion_matrix",
    "generate_classification_report",
    "generate_json_report",
    "save_visualizations",
    "collect_misclassified",
    "save_misclassified_csv",
    "save_json_report",
    "save_classification_report_text",
    "evaluate_model",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
