"""Dataset discovery API endpoints."""

from fastapi import APIRouter

from backend.api.dependencies import DatasetServiceDependency
from backend.schemas.datasets import (
    DatasetList,
    DatasetRefreshResponse,
    DatasetStatus,
    DatasetSummary,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.get(
    "",
    response_model=DatasetList,
    summary="List discovered datasets",
)
async def list_datasets(
    service: DatasetServiceDependency,
) -> DatasetList:
    """Return every dataset currently registered in memory."""
    return service.get_datasets()


@router.get(
    "/status",
    response_model=DatasetStatus,
    summary="Dataset availability counts",
)
async def datasets_status(
    service: DatasetServiceDependency,
) -> DatasetStatus:
    """Return available / missing / invalid / total counts."""
    return service.get_status()


@router.get(
    "/summary",
    response_model=DatasetSummary,
    summary="Dataset discovery summary",
)
async def datasets_summary(
    service: DatasetServiceDependency,
) -> DatasetSummary:
    """Return counts, file types, storage size, and discovery timestamp."""
    return service.get_summary()


@router.post(
    "/refresh",
    response_model=DatasetRefreshResponse,
    summary="Rescan dataset directories",
)
async def refresh_datasets(
    service: DatasetServiceDependency,
) -> DatasetRefreshResponse:
    """Rescan configured directories and refresh the in-memory registry."""
    dataset_list = service.refresh()
    return DatasetRefreshResponse(
        success=True,
        message="Dataset registry refreshed",
        data=dataset_list,
    )
