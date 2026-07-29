"""Load LightGBM artifacts and score removal / ordering candidates."""

from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any

from backend.core.config import Settings, get_settings
from backend.core.logging import get_logger
from ml.features.schema import (
    FEATURE_COLUMNS,
    REMOVAL_FEATURE_COLUMNS,
    ORDERING_FEATURE_COLUMNS,
    SEVERITY_MAP,
)

try:
    import lightgbm as lgb
except ImportError:  # pragma: no cover
    lgb = None  # type: ignore


class MlScoringService:
    """
    Optional ML scoring layer.

    When artifacts are missing or ml_enabled is false, callers should use heuristics.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._lock = RLock()
        self._removal_model: Any | None = None
        self._ordering_model: Any | None = None
        self._removal_meta: dict[str, Any] = {}
        self._ordering_meta: dict[str, Any] = {}
        self._loaded = False
        self._load_error: str | None = None

    @property
    def enabled(self) -> bool:
        return bool(self._settings.ml_enabled)

    @property
    def shadow_mode(self) -> bool:
        return bool(self._settings.ml_shadow_mode)

    @property
    def removal_blend(self) -> float:
        return float(self._settings.ml_removal_blend)

    @property
    def ordering_blend(self) -> float:
        return float(self._settings.ml_ordering_blend)

    def ensure_loaded(self) -> None:
        with self._lock:
            if self._loaded:
                return
            self._load_locked()

    def _load_locked(self) -> None:
        logger = get_logger()
        self._loaded = True
        if lgb is None:
            self._load_error = "lightgbm is not installed"
            logger.warning("ML scoring unavailable: %s", self._load_error)
            return

        artifacts = Path(self._settings.ml_artifacts_dir)
        removal_path = artifacts / "removal_classifier.txt"
        ordering_path = artifacts / "ordering_ranker.txt"
        try:
            if removal_path.exists():
                self._removal_model = lgb.Booster(model_file=str(removal_path))
                meta_path = artifacts / "removal_classifier_meta.json"
                if meta_path.exists():
                    self._removal_meta = json.loads(
                        meta_path.read_text(encoding="utf-8")
                    )
            if ordering_path.exists():
                self._ordering_model = lgb.Booster(model_file=str(ordering_path))
                meta_path = artifacts / "ordering_ranker_meta.json"
                if meta_path.exists():
                    self._ordering_meta = json.loads(
                        meta_path.read_text(encoding="utf-8")
                    )
            logger.info(
                "ML artifacts loaded removal=%s ordering=%s dir=%s",
                self._removal_model is not None,
                self._ordering_model is not None,
                artifacts,
            )
        except Exception as exc:  # noqa: BLE001
            self._load_error = str(exc)
            self._removal_model = None
            self._ordering_model = None
            logger.warning("Failed to load ML artifacts: %s", exc)

    def status(self) -> dict[str, Any]:
        self.ensure_loaded()
        return {
            "ml_enabled": self.enabled,
            "ml_shadow_mode": self.shadow_mode,
            "removal_model_loaded": self._removal_model is not None,
            "ordering_model_loaded": self._ordering_model is not None,
            "removal_blend": self.removal_blend,
            "ordering_blend": self.ordering_blend,
            "artifacts_dir": str(self._settings.ml_artifacts_dir),
            "load_error": self._load_error,
            "removal_meta": {
                "trained_at": self._removal_meta.get("trained_at"),
                "best_iteration": self._removal_meta.get("best_iteration"),
            },
            "ordering_meta": {
                "trained_at": self._ordering_meta.get("trained_at"),
                "best_iteration": self._ordering_meta.get("best_iteration"),
            },
        }

    def has_removal_model(self) -> bool:
        self.ensure_loaded()
        return self._removal_model is not None

    def has_ordering_model(self) -> bool:
        self.ensure_loaded()
        return self._ordering_model is not None

    def build_feature_row(
        self,
        payload: dict[str, Any],
        columns: list[str] | None = None,
    ) -> list[float]:
        """Build a dense feature vector matching training columns."""
        severity = str(payload.get("severity", "NONE"))
        values = {
            "fail_rate": float(payload.get("fail_rate", 0.0)),
            "severity_code": float(SEVERITY_MAP.get(severity, 0)),
            "mean_toggle_coverage": float(payload.get("mean_toggle_coverage", 0.0)),
            "mean_toggle_density": float(payload.get("mean_toggle_density", 0.0)),
            "mean_toggle_count": float(payload.get("mean_toggle_count", 0.0)),
            "coverage_percent": float(payload.get("coverage_percent", 0.0)),
            "failed_log_count": float(payload.get("failed_log_count", 0.0)),
            "failed_chain_count": float(payload.get("failed_chain_count", 0.0)),
            "total_executions": float(payload.get("total_executions", 0.0)),
            "fail_executions": float(payload.get("fail_executions", 0.0)),
            "similarity_to_representative": float(
                payload.get("similarity_to_representative", 0.0)
            ),
            "cluster_size": float(payload.get("cluster_size", 1.0)),
            "is_representative": float(payload.get("is_representative", 0.0)),
            "redundant_flag": float(payload.get("redundant_flag", 0.0)),
            "unique_fail_contribution": float(
                payload.get("unique_fail_contribution", 0.0)
            ),
            "normalized_unique_fail_contribution": float(
                payload.get("normalized_unique_fail_contribution", 0.0)
            ),
            "normalized_toggle_coverage": float(
                payload.get("normalized_toggle_coverage", 0.0)
            ),
            "heuristic_removal_priority": float(
                payload.get("heuristic_removal_priority", 0.0)
            ),
            "heuristic_order_score": float(payload.get("heuristic_order_score", 0.0)),
        }
        cols = columns or FEATURE_COLUMNS
        return [values[col] for col in cols]

    def predict_removal_proba(self, feature_rows: list[dict[str, Any]]) -> list[float]:
        self.ensure_loaded()
        if self._removal_model is None or not feature_rows:
            return []
        matrix = [
            self.build_feature_row(row, REMOVAL_FEATURE_COLUMNS) for row in feature_rows
        ]
        preds = self._removal_model.predict(matrix)
        return [float(x) for x in preds]

    def predict_ordering_scores(self, feature_rows: list[dict[str, Any]]) -> list[float]:
        self.ensure_loaded()
        if self._ordering_model is None or not feature_rows:
            return []
        matrix = [
            self.build_feature_row(row, ORDERING_FEATURE_COLUMNS) for row in feature_rows
        ]
        preds = self._ordering_model.predict(matrix)
        return [float(x) for x in preds]

    def blend_score(
        self,
        heuristic: float,
        ml_score: float | None,
        *,
        blend: float,
        unique_fail_contribution: float | None = None,
        for_removal: bool = False,
    ) -> float:
        """
        Blend heuristic and ML scores.

        Safety: for removal, unique_fail_contribution > 0 forces score toward keep (0).
        """
        if ml_score is None:
            return float(heuristic)
        alpha = max(0.0, min(1.0, float(blend)))
        blended = alpha * float(ml_score) + (1.0 - alpha) * float(heuristic)
        if for_removal and unique_fail_contribution is not None:
            if float(unique_fail_contribution) > 0:
                # Hard safety: never prefer remove when unique fails exist.
                blended = min(blended, float(heuristic) * 0.25)
        return round(max(0.0, min(1.0, blended)), 6)

    def should_apply(self) -> bool:
        """True when ML should influence returned API scores."""
        return self.enabled and not self.shadow_mode

    def should_shadow_log(self) -> bool:
        return self.enabled or self.shadow_mode


_ml_scoring_service: MlScoringService | None = None
_ml_lock = RLock()


def get_ml_scoring_service(settings: Settings | None = None) -> MlScoringService:
    global _ml_scoring_service
    with _ml_lock:
        if _ml_scoring_service is None:
            _ml_scoring_service = MlScoringService(settings or get_settings())
        return _ml_scoring_service


def reset_ml_scoring_service() -> None:
    global _ml_scoring_service
    with _ml_lock:
        _ml_scoring_service = None
