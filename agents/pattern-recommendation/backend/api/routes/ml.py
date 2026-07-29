"""ML status and operator feedback endpoints."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request

from backend.core.config import Settings, get_settings
from backend.schemas.ml import (
    MlFeedbackRequest,
    MlFeedbackResponse,
    MlStatusResponse,
)
from backend.services.ml_feedback_store import (
    MlFeedbackStore,
    get_ml_feedback_store,
)
from backend.services.ml_scoring_service import (
    MlScoringService,
    get_ml_scoring_service,
)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


def _resolve_ml_scoring(request: Request) -> MlScoringService:
    service = getattr(request.app.state, "ml_scoring_service", None)
    if isinstance(service, MlScoringService):
        return service
    return get_ml_scoring_service(get_settings())


def _resolve_feedback_store(request: Request) -> MlFeedbackStore:
    store = getattr(request.app.state, "ml_feedback_store", None)
    if isinstance(store, MlFeedbackStore):
        return store
    return get_ml_feedback_store(get_settings())


MlScoringDependency = Annotated[MlScoringService, Depends(_resolve_ml_scoring)]
MlFeedbackDependency = Annotated[MlFeedbackStore, Depends(_resolve_feedback_store)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get("/status", response_model=MlStatusResponse, summary="ML model status")
async def ml_status(service: MlScoringDependency) -> MlStatusResponse:
    return MlStatusResponse(success=True, data=service.status())


@router.post(
    "/feedback",
    response_model=MlFeedbackResponse,
    summary="Record operator accept/reject feedback",
)
async def ml_feedback(
    payload: MlFeedbackRequest,
    store: MlFeedbackDependency,
) -> MlFeedbackResponse:
    return store.record(payload)


@router.get("/feedback/recent", summary="Recent operator feedback rows")
async def ml_feedback_recent(
    store: MlFeedbackDependency,
    limit: int = 50,
) -> dict[str, Any]:
    rows = store.list_recent(limit=max(1, min(limit, 200)))
    return {"success": True, "total": len(rows), "rows": rows}
