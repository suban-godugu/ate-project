"""Dataset discovery response schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DatasetStatusValue = Literal["available", "missing", "invalid"]


class DatasetInfo(BaseModel):
    """Metadata for one discovered or expected dataset."""

    dataset_name: str
    dataset_type: str
    file_name: str
    absolute_path: str
    extension: str
    size_bytes: int = 0
    last_modified: str = ""
    status: DatasetStatusValue
    pattern: str = ""
    root: str = ""


class DatasetStatus(BaseModel):
    """Aggregate availability counts."""

    available: int = 0
    missing: int = 0
    invalid: int = 0
    total: int = 0


class DatasetSummary(BaseModel):
    """Discovery summary for dashboards and monitoring."""

    dataset_counts: DatasetStatus
    file_types: dict[str, int] = Field(default_factory=dict)
    total_storage_bytes: int = 0
    discovery_timestamp: datetime | None = None
    data_dir: str = ""
    output_dir: str = ""


class DatasetList(BaseModel):
    """Full registry payload."""

    datasets: list[DatasetInfo] = Field(default_factory=list)
    total: int = 0
    discovery_timestamp: datetime | None = None


class DatasetRefreshResponse(BaseModel):
    """Refresh acknowledgement with updated registry snapshot."""

    success: bool = True
    message: str
    data: DatasetList
