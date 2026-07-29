"""Reusable API response schemas."""

from typing import Any

from pydantic import BaseModel, Field


class SuccessResponse(BaseModel):
    """Common successful response envelope."""

    success: bool = True
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Common error response envelope."""

    success: bool = False
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Service health response."""

    status: str


class VersionResponse(BaseModel):
    """Application version response."""

    version: str


class RootResponse(BaseModel):
    """API discovery response."""

    project_name: str
    version: str
    status: str
    api: dict[str, str]
