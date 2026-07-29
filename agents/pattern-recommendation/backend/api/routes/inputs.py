"""Input inventory and connect endpoints for Pattern Recommendation Agent."""

from fastapi import APIRouter, HTTPException

from backend.api.dependencies import SettingsDependency
from backend.services.input_registry import connect_inputs, input_inventory

router = APIRouter(prefix="/inputs", tags=["Inputs"])


@router.get(
    "",
    summary="Show required Pattern Recommendation inputs",
)
async def get_inputs(settings: SettingsDependency) -> dict:
    """Inventory of PA-Analysis / PA-FR inputs under the shared input folder."""
    return input_inventory(settings)


@router.post(
    "/connect",
    summary="Connect inputs and refresh recommendation engines",
)
async def post_connect_inputs(settings: SettingsDependency) -> dict:
    """
    Validate on-disk inputs, build failure_summary.json if needed,
    refresh dataset/feature/recommendation caches.

    Inputs (under UPLOAD_INPUT_ROOT/pattern-recommendation):
      1. PA-Analysis-Session_executions.json
      2. PA-Analysis-Session_clustering.json
      3. PA-Analysis-Session_embeddings.json
      4. PA-FR-*_cpm_report.json
      5. PA-FR-*_cvm_cycles.csv
      6. PA-FR-*_metadata_metrics.json
    """
    result = connect_inputs(settings)
    if result.get("status") == "missing_inputs":
        raise HTTPException(status_code=400, detail=result)
    return result
