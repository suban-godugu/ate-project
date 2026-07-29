from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class GlobalFilters(BaseModel):
    date_preset: str = "7d"
    custom_date_from: str | None = None
    custom_date_to: str | None = None
    fab: str | None = None
    tester: str | None = None
    product: str | None = None
    lot: str | None = None
    wafer: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str
    department: str | None = None

    model_config = {"from_attributes": True}


class UserPreferencesUpdate(BaseModel):
    theme_json: dict | None = None
    account_json: dict | None = None
    filters_json: dict | None = None


class UserPreferencesOut(BaseModel):
    theme_json: dict | None = None
    account_json: dict | None = None
    filters_json: dict | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AuditLogOut(BaseModel):
    id: str
    action: str
    entity_type: str | None = None
    entity_id: str | None = None
    user_id: str | None = None
    username: str | None = None
    severity: str = "info"
    status: str | None = None
    message: str | None = None
    upload_job_id: str | None = None
    filename: str | None = None
    created_at: str | None = None
    meta: dict = Field(default_factory=dict)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    page: int
    page_size: int
    total: int


class KPIOut(BaseModel):
    id: str
    title: str
    value: str
    change: float
    trend: str
    sparkline: list[float] = Field(default_factory=list)
    icon: str | None = None
    positiveIsGood: bool | None = None


class DashboardTabResponse(BaseModel):
    kpis: list[KPIOut]
    rows: list[dict]
    charts: dict = Field(default_factory=dict)


class SearchResultItem(BaseModel):
    id: str
    title: str
    subtitle: str
    category: str
    route: str
    matchedField: str


class AlertCreate(BaseModel):
    source_module: str
    severity: str
    status: str = "Open"
    title: str | None = None
    description: str | None = None
    lot_id: str | None = None
    wafer_id: str | None = None
    assigned_user_id: str | None = None


class AlertUpdate(BaseModel):
    severity: str | None = None
    status: str | None = None
    title: str | None = None
    description: str | None = None
    assigned_user_id: str | None = None


class PresignRequest(BaseModel):
    file_name: str
    size: int
    module: str
    metadata: dict = Field(default_factory=dict)
    kind: str = "data"


class PresignResponse(BaseModel):
    job_id: str
    upload_url: str
    object_key: str


class CompleteUploadRequest(BaseModel):
    checksum_sha256: str | None = None


class PipelineStepOut(BaseModel):
    id: str
    label: str
    status: str


class UploadJobOut(BaseModel):
    id: str
    fileName: str
    module: str
    fileType: str | None = None
    size: str
    uploadedBy: str
    uploadTime: str
    status: str
    processingTime: str | None = None
    tester: str | None = None
    lotId: str | None = None
    waferId: str | None = None


class AILogSummaryOut(BaseModel):
    filesProcessed: str
    patternsFound: str
    scanChains: str
    memoryBlocks: str
    logicBlocks: str
    waferCount: str
    defectsFound: str
    yield_: str = Field(alias="yield")
    estimatedTestCost: str
    estimatedSavings: str

    model_config = ConfigDict(populate_by_name=True)


class JobCreatedResponse(BaseModel):
    job_id: str


class PrimaryActionResult(BaseModel):
    pageId: str
    label: str
    summary: str
    metrics: list[dict[str, str]]
    completedAt: str


class AIDiagnosisResult(BaseModel):
    rootCause: str
    confidence: float
    recommendation: str
    estimatedYieldImpact: str


class NotificationOut(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    read: bool
    timestamp: str
    alertRoute: str | None = None


class RecommendationFeedbackRequest(BaseModel):
    action_taken: str
    outcome_metric: str | None = None
    outcome_value: float | None = None


class ExportPDFRequest(BaseModel):
    title: str
    lines: list[str]


class ExportPDFResponse(BaseModel):
    url: str


class IntegrationHealthOut(BaseModel):
    name: str
    base_url: str
    embed_path: str | None = None
    api_url: str | None = None
    reachable: bool
    dashboard_present: bool
    docs_present: bool
    latency_ms: int | None = None
    status_code: int | None = None
    error: str | None = None
