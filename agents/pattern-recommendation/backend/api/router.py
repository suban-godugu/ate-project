"""Top-level API router."""

from fastapi import APIRouter

from backend.api.routes.coverage import router as coverage_router
from backend.api.routes.datasets import router as datasets_router
from backend.api.routes.failures import router as failures_router
from backend.api.routes.gap_analysis import router as gap_analysis_router
from backend.api.routes.inputs import router as inputs_router
from backend.api.routes.low_power import router as low_power_router
from backend.api.routes.ml import router as ml_router
from backend.api.routes.ordering import router as ordering_router
from backend.api.routes.orchestrator import router as orchestrator_router
from backend.api.routes.patterns import router as patterns_router
from backend.api.routes.redundancy import router as redundancy_router
from backend.api.routes.removal import router as removal_router
from backend.api.routes.system import router as system_router

api_router = APIRouter()
api_router.include_router(system_router)
api_router.include_router(inputs_router)
api_router.include_router(datasets_router)
api_router.include_router(patterns_router)
api_router.include_router(redundancy_router)
api_router.include_router(removal_router)
api_router.include_router(ordering_router)
api_router.include_router(gap_analysis_router)
api_router.include_router(low_power_router)
api_router.include_router(coverage_router)
api_router.include_router(failures_router)
api_router.include_router(ml_router)
# Unified orchestrator last so specific /recommendations/* routes win first.
api_router.include_router(orchestrator_router)
