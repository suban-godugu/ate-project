"""
Request schemas for the WaferVision-AI FastAPI backend.

Validation only — no business logic.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class GridMode(str, Enum):
    """Supported die-grid modes exposed by the API."""

    automatic = "automatic"
    manual = "manual"


class PredictRequestParams(BaseModel):
    """
    Multipart form fields accompanying an uploaded wafer image.

    Note: the image file itself is received as ``UploadFile`` in the route.
    """

    grid_mode: GridMode = Field(
        default=GridMode.automatic,
        description="Grid detection mode: automatic (default) or manual.",
        examples=["automatic"],
    )
    grid_size: Optional[int] = Field(
        default=None,
        ge=2,
        le=256,
        description="Square grid size for manual mode (rows = columns = grid_size).",
        examples=[52],
    )

    @field_validator("grid_mode", mode="before")
    @classmethod
    def _normalize_grid_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def _require_grid_size_for_manual(self) -> "PredictRequestParams":
        if self.grid_mode == GridMode.manual and self.grid_size is None:
            raise ValueError(
                "grid_size is required when grid_mode is 'manual' "
                "(example: grid_size=52)."
            )
        if self.grid_mode == GridMode.automatic and self.grid_size is not None:
            # Allow but ignore is friendlier; prompt says only required for manual.
            # Keep value — pipeline ignores it in automatic mode.
            pass
        return self


class BatchPredictRequestParams(BaseModel):
    """Shared grid parameters for batch uploads."""

    grid_mode: GridMode = Field(default=GridMode.automatic, examples=["automatic"])
    grid_size: Optional[int] = Field(default=None, ge=2, le=256, examples=[52])

    @field_validator("grid_mode", mode="before")
    @classmethod
    def _normalize_grid_mode(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @model_validator(mode="after")
    def _require_grid_size_for_manual(self) -> "BatchPredictRequestParams":
        if self.grid_mode == GridMode.manual and self.grid_size is None:
            raise ValueError(
                "grid_size is required when grid_mode is 'manual'."
            )
        return self


class HealthResponse(BaseModel):
    """GET / health payload."""

    message: str = Field(examples=["WaferVision-AI API Running"])


class VersionResponse(BaseModel):
    """GET /version payload."""

    name: str = Field(examples=["WaferVision-AI"])
    version: str = Field(examples=["1.0.0"])
    model_version: str = Field(examples=["1.0.0"])
    environment: str = Field(examples=["development"])
    api: str = Field(examples=["v1"])


class MetricsResponse(BaseModel):
    """GET /metrics payload (fields vary with optional psutil)."""

    version: str = Field(examples=["1.0.0"])
    uptime_seconds: float = Field(examples=[12.5])
    model_loaded: bool = Field(examples=[True])
    pid: int = Field(examples=[1234])


class ErrorResponse(BaseModel):
    """Structured production error body."""

    status: str = Field(examples=["error"])
    message: str = Field(examples=["Unsupported image format."])
    code: int = Field(examples=[415])
    detail: str = Field(
        examples=["Unsupported image format."],
        description="Alias of message for legacy clients",
    )


__all__ = [
    "GridMode",
    "PredictRequestParams",
    "BatchPredictRequestParams",
    "HealthResponse",
    "VersionResponse",
    "MetricsResponse",
    "ErrorResponse",
]
