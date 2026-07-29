"""
Response models for WaferVision-AI FastAPI OpenAPI documentation.

These models document the shape of ``run_wafer_analysis()`` JSON.
Runtime responses return the pipeline dictionary unchanged (including future
keys such as clusters / zone_analysis) so the API never strips fields.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ClassificationResult(BaseModel):
    """Wafer-level CNN classification."""

    model_config = ConfigDict(extra="allow")

    defect_type: str = Field(examples=["Center"])
    confidence: float = Field(examples=[99.91])
    class_index: Optional[int] = Field(default=None, examples=[0])


class YieldSummary(BaseModel):
    """Die yield statistics."""

    model_config = ConfigDict(extra="allow")

    good_dies: int = Field(examples=[1515])
    fail_dies: int = Field(examples=[413])
    total_dies: int = Field(examples=[1928])
    yield_percent: float = Field(examples=[78.58])


class GridInfo(BaseModel):
    """Detected or manual grid metadata."""

    model_config = ConfigDict(extra="allow")

    mode: str = Field(examples=["automatic"])
    rows: int = Field(examples=[48])
    columns: int = Field(examples=[48])
    pitch: float = Field(examples=[4.0])
    offset_x: float = Field(examples=[0.0])
    offset_y: float = Field(examples=[1.0])


class WaferGeometry(BaseModel):
    """Circular wafer geometry."""

    model_config = ConfigDict(extra="allow")

    center_x: float = Field(examples=[113.0])
    center_y: float = Field(examples=[113.0])
    radius: float = Field(examples=[102.0])


class Die(BaseModel):
    """Single die record."""

    model_config = ConfigDict(extra="allow")

    die_id: int = Field(examples=[1])
    row: int = Field(examples=[12])
    column: int = Field(examples=[15])
    x: int = Field(examples=[104])
    y: int = Field(examples=[87])
    status: str = Field(examples=["FAIL"])
    bbox: Optional[dict[str, int]] = None


class ImageSet(BaseModel):
    """Deprecated compatibility bundle for clients that still require PNGs."""

    model_config = ConfigDict(extra="allow")

    original: Optional[str] = None
    overlay: Optional[str] = None
    density: Optional[str] = None
    gradcam: Optional[str] = None
    heatmap: Optional[str] = None


class VisualizationData(BaseModel):
    """Renderer-neutral layered visualization contract."""

    model_config = ConfigDict(extra="allow")

    version: int = 1
    coordinate_space: dict[str, Any]
    rendering: dict[str, Any]
    original: dict[str, Any]
    failure_overlay: dict[str, Any]
    density: dict[str, Any]
    gradcam: dict[str, Any]


class Clusters(BaseModel):
    """Placeholder for future spatial cluster payloads."""

    model_config = ConfigDict(extra="allow")

    items: list[dict[str, Any]] = Field(default_factory=list)


class ZoneAnalysis(BaseModel):
    """Placeholder for future engineering zone payloads."""

    model_config = ConfigDict(extra="allow")

    zones: dict[str, Any] = Field(default_factory=dict)


class PredictionResponse(BaseModel):
    """
    Documented response shape for single-wafer analysis.

    ``extra='allow'`` ensures future pipeline keys are accepted by the schema
    without API code changes.
    """

    model_config = ConfigDict(extra="allow")

    wafer_id: str = Field(examples=["wafer.png"])
    classification: ClassificationResult
    yield_summary: YieldSummary
    grid_info: GridInfo
    wafer_geometry: WaferGeometry
    dies: list[Die] = Field(default_factory=list)
    visualization: Optional[VisualizationData] = None
    images: Optional[ImageSet] = None
    clusters: Optional[Clusters] = None
    zone_analysis: Optional[ZoneAnalysis] = None


class BatchPredictionResponse(BaseModel):
    """List of wafer analysis results."""

    model_config = ConfigDict(extra="allow")

    results: list[PredictionResponse]


__all__ = [
    "ClassificationResult",
    "YieldSummary",
    "GridInfo",
    "WaferGeometry",
    "Die",
    "ImageSet",
    "VisualizationData",
    "Clusters",
    "ZoneAnalysis",
    "PredictionResponse",
    "BatchPredictionResponse",
]
