"""ML status and operator feedback schemas."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

FeedbackDecision = Literal["accept", "reject", "edit"]
FeedbackDomain = Literal["removal", "ordering"]


class MlStatusResponse(BaseModel):
    """Runtime ML artifact / config status."""

    success: bool = True
    data: dict[str, Any] = Field(default_factory=dict)


class MlFeedbackRequest(BaseModel):
    """Operator label for a removal or ordering recommendation."""

    domain: FeedbackDomain
    pattern_id: str
    decision: FeedbackDecision
    note: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class MlFeedbackResponse(BaseModel):
    success: bool = True
    message: str
    recorded_at: datetime | None = None
