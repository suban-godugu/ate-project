import os
import json
import time
import shutil
import csv
import concurrent.futures
from datetime import datetime, timezone
from io import BytesIO
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from stil_parser import STILParser
from ate_parser import ATEParser
from coverage_calculator import CoverageCalculator

app = FastAPI(title="Pattern Analysis Agent API", version="1.0.0")

from pipeline.consume_api import router as pipeline_router
from pipeline.run_api import router as pattern_run_router

app.include_router(pipeline_router)
app.include_router(pattern_run_router)

WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(WORKSPACE_DIR, "config.json")
UPLOAD_DIR = os.path.join(WORKSPACE_DIR, "uploads")
STIL_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "stil")
ATE_UPLOAD_DIR = os.path.join(UPLOAD_DIR, "ate_logs")
OUTPUT_DIR = os.path.join(WORKSPACE_DIR, "output")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(STIL_UPLOAD_DIR, exist_ok=True)
os.makedirs(ATE_UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

from scan_vector_cache import write_scan_vector_cache
from pattern_embedding import generate_pattern_embeddings
from embedding_validation import validate_pattern_embeddings
from embedding_diagnostics_presentation import enrich_validation_presentation
from cluster_exporter import run_pattern_clustering, get_clustering_configuration
from redundancy_exporter import run_pattern_redundancy
from redundancy_engine import RedundancyAbortedError
from cluster_engine import (
    ClusteringAbortedError,
    ClusteringConfigError,
    EMBEDDINGS_FILENAME,
    persist_similarity_threshold,
)
from similarity_api import (
    handle_pair_similarity,
    handle_top_n_similarity,
)
from similarity_config import load_similarity_config
from similarity_validator import SimilarityAbortError, SimilarityValidationError
from session_similarity_engine import (
    SessionSimilarityEngine,
    session_unit_id,
    source_lot,
)
from canonical_hash_startup import run_canonical_hash_startup_verification
from compute_device import get_device_info, log_compute_device_at_startup, reset_device_cache
from correlation_exporter import CorrelationAbortedError, handle_correlate_pattern_outcomes
from report_model_builder import (
    REPORT_MODEL_FILENAME,
    write_pattern_quality_report_model,
)
from report_preview_builder import (
    ReportPreviewError,
    build_report_preview_from_output,
    load_report_model,
)
from analysis_session_report_preview_builder import (
    AnalysisSessionReportPreviewError,
    preview_analysis_session_report_from_output,
)
from analysis_session_report_generator import (
    AnalysisSessionReportGenerationError,
    AnalysisSessionReportModelError,
    generate_analysis_session_report_from_output,
)
# PA-FR-010.AS.5 START
from analysis_session_report_history import (
    HISTORY_FILENAME as ANALYSIS_SESSION_HISTORY_FILENAME,
    HISTORY_GENERATOR as ANALYSIS_SESSION_HISTORY_GENERATOR,
    HISTORY_VERSION as ANALYSIS_SESSION_HISTORY_VERSION,
    AnalysisSessionReportHistoryError,
    append_analysis_session_report_history,
    delete_analysis_session_report_history_entry,
    get_analysis_session_report_history,
    get_analysis_session_report_history_entry,
)
# PA-FR-010.AS.5 END
# PA-UI-011 START
from pattern_analysis_master_exporter import MASTER_FILENAME, export_pattern_analysis_master
# PA-UI-011 END
from report_generator import (
    ReportGenerationError,
    generate_report_from_output,
)
from report_history import (
    HISTORY_FILENAME,
    HISTORY_GENERATOR,
    HISTORY_VERSION,
    ReportHistoryError,
    add_history_entry,
    create_history_record,
    delete_history_entry,
    get_history_entry,
    list_history,
)
from analysis_session import (
    SESSION_ARTIFACT_FILENAMES,
    SESSION_CLUSTERING_JSON,
    SESSION_CORRELATION_JSON,
    SESSION_EMBEDDINGS_JSON,
    SESSION_EXECUTIONS_JSON,
    SESSION_REDUNDANCY_JSON,
    SessionPathError,
)
from session_artifact_exporter import run_analysis_session_pipeline
from session_correlation_exporter import build_session_correlation_analytics
from session_downstream_adapter import prepare_session_downstream, session_runtime_dir
from session_request import resolve_selected_ate_logs, should_use_session_path
import traceback
import hashlib

from analysis_job_progress import (
    install_session_perf_trace_hooks,
    load_phase_weights_from_perf_trace,
    progress_job_context,
    progress_manager,
)
from robustness_config import load_robustness_config, lot_from_relpath

install_session_perf_trace_hooks()

_ANALYSIS_JOB_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="paa-analysis-job",
)

_ROBUSTNESS_CFG = load_robustness_config(WORKSPACE_DIR)

# Session executions/embeddings stay on disk / in-memory cache — never inlined into parse-workspace JSON.
_SESSION_EXECUTIONS_CACHE: List[Dict[str, Any]] = []
_SESSION_EXECUTIONS_CACHE_HASH: Optional[str] = None
_SESSION_EMBEDDINGS_CACHE: List[Dict[str, Any]] = []
_SESSION_EMBEDDINGS_META: Dict[str, Any] = {}
_SESSION_REDUNDANCY_CACHE: List[Dict[str, Any]] = []
_SESSION_REDUNDANCY_META: Dict[str, Any] = {}
_SESSION_SIMILARITY_CLUSTER_LOOKUP: Dict[str, str] = {}
_SESSION_SIMILARITY_ENGINE: Optional[SessionSimilarityEngine] = None
_SESSION_CORRELATION_CACHE: List[Dict[str, Any]] = []
_SESSION_CORRELATION_META: Dict[str, Any] = {}


class CorrelatePatternOutcomesRequest(BaseModel):
    ate_log_paths: Optional[list[str]] = None
    input_stil: Optional[str] = ""


class ReportGenerateRequest(BaseModel):
    format: str


@app.on_event("startup")
async def _verify_canonical_hash_on_startup() -> None:
    log_compute_device_at_startup()
    run_canonical_hash_startup_verification()


@app.get("/api/compute/device")
def api_compute_device():
    """Report resolved CPU/CUDA compute device for acceleration paths."""
    reset_device_cache()
    return get_device_info().to_dict()


def run_pa_fr_007_extensions(report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    clustering = report.get("pattern_clustering")
    if not clustering or clustering.get("status") == "ABORTED":
        return None
    try:
        return run_pattern_redundancy(OUTPUT_DIR, WORKSPACE_DIR)
    except RedundancyAbortedError as exc:
        print(f"PA-FR-007 redundancy aborted: {exc}")
        return {"generated_by": "PA-FR-007", "status": "ABORTED", "error": str(exc)}
    except Exception as exc:
        print(f"Error running PA-FR-007 extensions: {str(exc)}")
        return None


def run_pa_fr_006_extensions(report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not report.get("pattern_embeddings"):
        return None
    try:
        return run_pattern_clustering(OUTPUT_DIR, WORKSPACE_DIR)
    except ClusteringAbortedError as exc:
        print(f"PA-FR-006 clustering aborted: {exc}")
        return {"generated_by": "PA-FR-006", "status": "ABORTED", "error": str(exc)}
    except Exception as exc:
        print(f"Error running PA-FR-006 extensions: {str(exc)}")
        return None

def run_pa_fr_005_extensions(report: Dict[str, Any], ate_log_path: Optional[str]) -> Optional[Dict[str, Any]]:
    if report.get("status") != "PASS" or "toggle_coverage" not in report:
        return None
    try:
        write_scan_vector_cache(OUTPUT_DIR, ate_log_path, report.get("file_name", ""))
        return generate_pattern_embeddings(OUTPUT_DIR)
    except Exception as exc:
        print(f"Error running PA-FR-005 extensions: {str(exc)}")
        return None

def run_pa_fr_005_validation() -> Optional[Dict[str, Any]]:
    try:
        started_at = time.time()
        validation_report = validate_pattern_embeddings(OUTPUT_DIR)
        if validation_report:
            return enrich_validation_presentation(validation_report, OUTPUT_DIR, started_at)
        return validation_report
    except Exception as exc:
        print(f"Error running PA-FR-005 embedding validation: {str(exc)}")
        return None

def write_requirement_outputs(report: Dict[str, Any]):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. Requirement 1 (PA-FR-001) - CPM Structural Report
    cpm_data = {
        "generated_by": "PA-FR-001",
        "file_name": report.get("file_name"),
        "file_size_bytes": report.get("file_size_bytes"),
        "line_count": report.get("line_count"),
        "status": report.get("status"),
        "signals_count": report.get("signals_count"),
        "groups_count": report.get("groups_count"),
        "scan_chains_count": report.get("scan_chains_count"),
        "patterns_count": report.get("patterns_count"),
        "signals": report.get("signals"),
        "signal_groups": report.get("signal_groups"),
        "scan_chains": report.get("scan_chains"),
        "timing_tables": report.get("timing_tables"),
        "referenced_timing_sets": report.get("referenced_timing_sets"),
        "external_timing_references": report.get("external_timing_references"),
        "timing_validation_mode": report.get("timing_validation_mode"),
        "errors": report.get("errors"),
        "warnings": report.get("warnings"),
        "warning_count": report.get("warning_count"),
        "structural_validation_pass_ratio": report.get("structural_validation_pass_ratio")
    }
    cpm_path = os.path.join(OUTPUT_DIR, "PA-FR-001_cpm_report.json")
    with open(cpm_path, "w", encoding="utf-8") as f:
        json.dump(cpm_data, f, indent=2)

    # 2. Requirement 2 (PA-FR-002) - CVM Classified Vectors (CSV)
    cvm_path = os.path.join(OUTPUT_DIR, "PA-FR-002_cvm_cycles.csv")
    with open(cvm_path, "w", encoding="utf-8", newline="") as f:
        f.write("# Generated by requirement: PA-FR-002\n")
        writer = csv.writer(f)
        writer.writerow(["cycle_number", "cycle_type", "vector_type", "assignments"])
        for cycle in report.get("cycles", []):
            assignments_str = json.dumps(cycle.get("assignments", {}))
            writer.writerow([
                cycle.get("cycle_number"),
                cycle.get("cycle_type"),
                cycle.get("vector_type"),
                assignments_str
            ])

    # 3. Requirement 3 (PA-FR-003) - Features & Metadata Metrics
    meta_src = report.get("metadata", {})
    metadata_data = {
        "generated_by": "PA-FR-003",
        "pattern_count": meta_src.get("pattern_count"),
        "chain_count": meta_src.get("chain_count"),
        "max_chain_length": meta_src.get("max_chain_length"),
        "total_flip_flops": meta_src.get("total_flip_flops"),
        "external_channels": meta_src.get("external_channels"),
        "compression_ratio": meta_src.get("compression_ratio"),
        "vector_count": meta_src.get("vector_count"),
        "scan_in_pins": meta_src.get("scan_in_pins"),
        "scan_out_pins": meta_src.get("scan_out_pins")
    }
    metadata_path = os.path.join(OUTPUT_DIR, "PA-FR-003_metadata_metrics.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata_data, f, indent=2)

    # 4. Requirement 4 (PA-FR-004) - Toggle Coverage Report (JSON & CSVs)
    if "toggle_coverage" in report:
        tc = report["toggle_coverage"]
        cov_data = {
            "generated_by": "PA-FR-004",
            "file_rollup": tc.get("file_rollup"),
            "pattern_level": tc.get("pattern_level"),
            "scan_chain_level": tc.get("scan_chain_level")
        }
        cov_path = os.path.join(OUTPUT_DIR, "PA-FR-004_toggle_coverage.json")
        with open(cov_path, "w", encoding="utf-8") as f:
            json.dump(cov_data, f, indent=2)
            
        # 4B. Export CSV for File Rollup
        rollup_path = os.path.join(OUTPUT_DIR, "PA-FR-004_file_rollup.csv")
        with open(rollup_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "file_name", "total_toggle_count", "toggle_coverage_pct", 
                "toggle_density_pct", "patterns_analyzed", "scan_chains_analyzed"
            ])
            fr = tc.get("file_rollup", {})
            writer.writerow([
                fr.get("file_name"), fr.get("total_toggle_count"), fr.get("toggle_coverage_pct"),
                fr.get("toggle_density_pct"), fr.get("patterns_analyzed"), fr.get("scan_chains_analyzed")
            ])
            
        # 4C. Export CSV for Pattern Level
        pat_path = os.path.join(OUTPUT_DIR, "PA-FR-004_pattern_level.csv")
        with open(pat_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["pattern_id", "toggle_count", "toggle_coverage_pct", "toggle_density_pct"])
            for pat in tc.get("pattern_level", []):
                writer.writerow([
                    pat.get("pattern_id"), pat.get("toggle_count"),
                    pat.get("toggle_coverage_pct"), pat.get("toggle_density_pct")
                ])
                
        # 4D. Export CSV for Scan Chain Level
        chain_path = os.path.join(OUTPUT_DIR, "PA-FR-004_scan_chain_level.csv")
        with open(chain_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["pattern_id", "scan_chain_id", "toggle_count", "toggle_coverage_pct", "toggle_density_pct"])
            for ch in tc.get("scan_chain_level", []):
                writer.writerow([
                    ch.get("pattern_id"), ch.get("scan_chain_id"), ch.get("toggle_count"),
                    ch.get("toggle_coverage_pct"), ch.get("toggle_density_pct")
                ])

class WorkspaceFileRequest(BaseModel):
    filename: str
    ate_log_filename: Optional[str] = None
    ate_log_filenames: Optional[list[str]] = None

class ConfigUpdateRequest(BaseModel):
    max_file_size_gb: float
    max_ate_file_size_gb: float

class ReclusterRequest(BaseModel):
    similarity_threshold: float

class SimilarityPairRequest(BaseModel):
    pattern_a: str
    pattern_b: str

class SimilarityTopNRequest(BaseModel):
    reference_pattern: str
    top_n: Optional[int] = None

class SessionSimilarityPairRequest(BaseModel):
    unit_a: str
    unit_b: str

class SessionSimilarityTopNRequest(BaseModel):
    reference_unit: str
    top_n: Optional[int] = None

def load_config() -> Dict[str, Any]:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                cfg = json.load(f)
                if "max_file_size_gb" not in cfg:
                    cfg["max_file_size_gb"] = 10.0
                if "max_ate_file_size_gb" not in cfg:
                    cfg["max_ate_file_size_gb"] = 10.0
                return cfg
        except Exception:
            pass
    return {"max_file_size_gb": 10.0, "max_ate_file_size_gb": 10.0}

def save_config(config: Dict[str, Any]):
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

@app.get("/api/config")
def get_config():
    return load_config()

@app.post("/api/config")
def update_config(req: ConfigUpdateRequest):
    if req.max_file_size_gb <= 0 or req.max_ate_file_size_gb <= 0:
        raise HTTPException(status_code=400, detail="Sizes must be greater than 0")
    config = {
        "max_file_size_gb": req.max_file_size_gb,
        "max_ate_file_size_gb": req.max_ate_file_size_gb
    }
    save_config(config)
    return {"status": "success", "config": config}

@app.get("/api/clustering/config")
def get_clustering_config():
    """Return the current clustering configuration and embeddings availability."""
    return get_clustering_configuration(WORKSPACE_DIR, OUTPUT_DIR)

@app.post("/api/clustering/recluster")
def recluster_with_threshold(req: ReclusterRequest):
    """
    Persist a new similarity threshold and re-run PA-FR-006 only.
    Uses existing PA-FR-005 embeddings; does not regenerate embeddings or rerun PA-FR-001..005.
    """
    embeddings_path = os.path.join(OUTPUT_DIR, EMBEDDINGS_FILENAME)
    if not os.path.exists(embeddings_path):
        raise HTTPException(
            status_code=400,
            detail="No PA-FR-005 embeddings found. Run the pipeline through PA-FR-005 first.",
        )

    config_path = os.path.join(WORKSPACE_DIR, "config", "clustering.yaml")
    try:
        persist_similarity_threshold(config_path, req.similarity_threshold)
    except ClusteringConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        clustering_summary = run_pattern_clustering(OUTPUT_DIR, WORKSPACE_DIR)
    except ClusteringAbortedError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {exc}") from exc

    if clustering_summary.get("status") == "ABORTED":
        raise HTTPException(
            status_code=400,
            detail=clustering_summary.get("error", "Clustering aborted."),
        )

    redundancy_summary = run_pa_fr_007_extensions({"pattern_clustering": clustering_summary})

    response = {
        "status": "success",
        "similarity_threshold": req.similarity_threshold,
        "pattern_clustering": clustering_summary,
    }
    if redundancy_summary:
        response["pattern_redundancy"] = redundancy_summary
    return response

def _is_stil_filename(filename: str) -> bool:
    return filename.lower().endswith(".stil")


def _is_log_filename(filename: str) -> bool:
    return filename.lower().endswith(".log")


def _collect_workspace_ate_logs() -> List[str]:
    """Return absolute paths to all ATE logs under ate_log_files/ and uploads/ate_logs/."""
    ate_log_files: list[str] = []
    ate_dir = os.path.join(WORKSPACE_DIR, "ate_log_files")
    if os.path.exists(ate_dir):
        for root, _dirs, files in os.walk(ate_dir):
            for f in files:
                if _is_log_filename(f):
                    ate_log_files.append(os.path.join(root, f))
    if os.path.exists(ATE_UPLOAD_DIR):
        for f in os.listdir(ATE_UPLOAD_DIR):
            if _is_log_filename(f):
                ate_log_files.append(os.path.join(ATE_UPLOAD_DIR, f))
    ate_log_files = sorted(set(ate_log_files))
    return ate_log_files


def _append_stil_file_entry(
    files_list: List[Dict[str, Any]],
    full_path: str,
    *,
    source: str,
    display_name: Optional[str] = None,
) -> None:
    rel_path = os.path.relpath(full_path, WORKSPACE_DIR).replace("\\", "/")
    stat = os.stat(full_path)
    entry: Dict[str, Any] = {
        "filename": rel_path,
        "display_name": display_name or rel_path,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified_time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
        "source": source,
    }
    files_list.append(entry)


@app.get("/api/files")
def list_files():
    """Lists all .stil files in the workspace root and uploads/stil/."""
    files_list: List[Dict[str, Any]] = []
    for f in os.listdir(WORKSPACE_DIR):
        if _is_stil_filename(f):
            _append_stil_file_entry(
                files_list,
                os.path.join(WORKSPACE_DIR, f),
                source="workspace",
            )
    if os.path.exists(STIL_UPLOAD_DIR):
        for f in os.listdir(STIL_UPLOAD_DIR):
            if _is_stil_filename(f):
                _append_stil_file_entry(
                    files_list,
                    os.path.join(STIL_UPLOAD_DIR, f),
                    source="upload",
                    display_name=f"Uploaded: {f}",
                )
    files_list.sort(key=lambda item: item["filename"].lower())
    return files_list

@app.get("/api/ate-files")
def list_ate_files():
    """Lists all ATE log .log files recursively in ate_log_files and uploads/ate_logs/."""
    files_list = []
    ate_dir = os.path.join(WORKSPACE_DIR, "ate_log_files")
    if os.path.exists(ate_dir):
        for root, _dirs, files in os.walk(ate_dir):
            for f in files:
                if _is_log_filename(f):
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
                    stat = os.stat(full_path)
                    files_list.append({
                        "filename": rel_path.replace("\\", "/"),
                        "display_name": os.path.relpath(full_path, ate_dir).replace("\\", "/"),
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "source": "workspace"
                    })
    if os.path.exists(ATE_UPLOAD_DIR):
        for f in os.listdir(ATE_UPLOAD_DIR):
            if _is_log_filename(f):
                full_path = os.path.join(ATE_UPLOAD_DIR, f)
                rel_path = os.path.relpath(full_path, WORKSPACE_DIR)
                stat = os.stat(full_path)
                files_list.append({
                    "filename": rel_path.replace("\\", "/"),
                    "display_name": f"Uploaded: {f}",
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "source": "upload"
                })
    return files_list

@app.post("/api/upload-ate")
async def upload_ate_file(file: UploadFile = File(...)):
    if not _is_log_filename(file.filename or ""):
        raise HTTPException(status_code=400, detail="Only ATE log .log files are supported")
        
    config = load_config()
    max_gb = config.get("max_ate_file_size_gb", 10.0)
    
    temp_file_path = os.path.join(ATE_UPLOAD_DIR, file.filename)
    
    try:
        # Save in chunks
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Verify size limit
        file_size = os.path.getsize(temp_file_path)
        limit_bytes = max_gb * 1024 * 1024 * 1024
        if file_size > limit_bytes:
            os.remove(temp_file_path)
            raise HTTPException(
                status_code=400, 
                detail=f"ATE log file size ({round(file_size / (1024*1024), 2)} MB) exceeds configured limit ({max_gb} GB)"
            )
            
        return {
            "status": "success",
            "filename": os.path.relpath(temp_file_path, WORKSPACE_DIR).replace("\\", "/"),
            "size_bytes": file_size
        }
    except HTTPException:
        raise
    except Exception as e:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Failed to save ATE upload: {str(e)}")

def calculate_and_attach_coverage(
    report: Dict[str, Any],
    manual_ate_filename: str = None,
    *,
    require_ate: bool = True,
) -> Optional[str]:
    if report.get("status") != "PASS":
        return None
    
    # Try to find a matching ATE log
    pat_count = report.get("patterns_count", 0)
    ate_log_path = None
    
    # 1. If manual file name is provided, resolve its path
    if manual_ate_filename:
        path_opt1 = os.path.join(WORKSPACE_DIR, manual_ate_filename)
        path_opt2 = os.path.join(ATE_UPLOAD_DIR, os.path.basename(manual_ate_filename))
        if os.path.exists(path_opt1):
            ate_log_path = path_opt1
        elif os.path.exists(path_opt2):
            ate_log_path = path_opt2
        else:
            # Fallback to direct path in case of full path
            ate_log_path = os.path.join(WORKSPACE_DIR, manual_ate_filename.replace("/", os.sep))
            
    # Check size and presence of manual_ate_filename
    if manual_ate_filename and (not ate_log_path or not os.path.exists(ate_log_path)):
        raise HTTPException(
            status_code=400,
            detail=f"Selected ATE log '{manual_ate_filename}' was not found in the workspace.",
        )
    if ate_log_path and os.path.exists(ate_log_path):
        config = load_config()
        max_gb = config.get("max_ate_file_size_gb", 10.0)
        file_size = os.path.getsize(ate_log_path)
        limit_bytes = max_gb * 1024 * 1024 * 1024
        if file_size > limit_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"Selected ATE log file size ({round(file_size / (1024*1024), 2)} MB) exceeds configured limit ({max_gb} GB)"
            )
    elif not manual_ate_filename:
        # Auto-detect only when exactly one ATE log exists across workspace + uploads.
        ate_log_files = _collect_workspace_ate_logs()
        if len(ate_log_files) == 1:
            ate_log_path = ate_log_files[0]
            config = load_config()
            max_gb = config.get("max_ate_file_size_gb", 10.0)
            file_size = os.path.getsize(ate_log_path)
            limit_bytes = max_gb * 1024 * 1024 * 1024
            if file_size > limit_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"Auto-detected ATE log file size ({round(file_size / (1024*1024), 2)} MB) exceeds configured limit ({max_gb} GB)"
                )
        elif not ate_log_files:
            if require_ate:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "No ATE logs found. Upload an ATE log, place one under ate_log_files/, "
                        "or provide ate_log_filename/ate_log_filenames."
                    ),
                )
            report["ate_coverage_status"] = {
                "attached": False,
                "reason": "no_ate_logs",
                "message": "STIL parsed without ATE coverage (no ATE logs in workspace).",
            }
            return None
        else:
            if require_ate:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Multiple ATE logs found. Select ATE log(s) in the workspace ingest panel "
                        "or provide ate_log_filename/ate_log_filenames explicitly."
                    ),
                )
            report["ate_coverage_status"] = {
                "attached": False,
                "reason": "multiple_ate_logs_unselected",
                "message": (
                    "STIL parsed without ATE coverage. Select an ATE log in the workspace "
                    "ingest panel and use Validate Ingestion for full coverage analysis."
                ),
            }
            return None

    if ate_log_path and os.path.exists(ate_log_path):
        try:
            print(f"Loading ATE log for coverage calculation: {ate_log_path}")
            ate_parser = ATEParser()
            cov_calc = CoverageCalculator()
            
            ate_data = ate_parser.parse(ate_log_path)
            coverage_report = cov_calc.calculate_coverage(ate_data)
            coverage_report["file_rollup"]["file_name"] = report.get("file_name", "")
            
            report["toggle_coverage"] = coverage_report
            if "metadata" in report:
                report["metadata"]["toggle_coverage_pct"] = coverage_report["file_rollup"]["toggle_coverage_pct"]
                report["metadata"]["toggle_density_pct"] = coverage_report["file_rollup"]["toggle_density_pct"]
                report["metadata"]["total_toggle_count"] = coverage_report["file_rollup"]["total_toggle_count"]
                report["metadata"]["ate_log_used"] = os.path.basename(ate_log_path)
            report["ate_coverage_status"] = {
                "attached": True,
                "reason": "attached",
                "message": f"Toggle coverage computed from {os.path.basename(ate_log_path)}.",
                "ate_log_filename": os.path.relpath(ate_log_path, WORKSPACE_DIR).replace("\\", "/"),
            }
            return ate_log_path
        except Exception as e:
            print(f"Error calculating coverage: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error performing toggle coverage calculations: {str(e)}")
    return None

def _clear_session_artifacts(output_dir: str) -> None:
    """Remove multi-log session outputs so legacy single-log correlation is not poisoned."""
    for name in SESSION_ARTIFACT_FILENAMES:
        path = os.path.join(output_dir, name)
        if os.path.exists(path):
            os.remove(path)
    runtime = session_runtime_dir(output_dir)
    if os.path.isdir(runtime):
        shutil.rmtree(runtime, ignore_errors=True)


def _enforce_ate_log_size_limit(ate_log_path: str) -> None:
    config = load_config()
    max_gb = config.get("max_ate_file_size_gb", 10.0)
    file_size = os.path.getsize(ate_log_path)
    limit_bytes = max_gb * 1024 * 1024 * 1024
    if file_size > limit_bytes:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Selected ATE log file size ({round(file_size / (1024*1024), 2)} MB) "
                f"exceeds configured limit ({max_gb} GB)"
            ),
        )


def _build_session_coverage_kpis(executions: List[Dict[str, Any]]) -> Dict[str, Any]:
    coverages = [
        float(row["toggle_coverage_pct"])
        for row in executions
        if row.get("toggle_coverage_pct") is not None
    ]
    pass_count = sum(1 for row in executions if row.get("latest_result") == "PASS")
    fail_count = sum(1 for row in executions if row.get("latest_result") == "FAIL")
    kpis: Dict[str, Any] = {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "execution_record_count": len(executions),
    }
    if coverages:
        kpis["toggle_coverage_pct_avg"] = round(sum(coverages) / len(coverages), 4)
        kpis["toggle_coverage_pct_max"] = round(max(coverages), 4)
        kpis["toggle_coverage_pct_min"] = round(min(coverages), 4)
    return kpis


def _lot_label_from_relpath(relpath: str) -> str:
    return lot_from_relpath(relpath, config=_ROBUSTNESS_CFG)


def _embedding_row_hash(row: Dict[str, Any]) -> str:
    vec = row.get("embedding")
    if isinstance(vec, list) and vec:
        digest = hashlib.sha256()
        for value in vec:
            digest.update(f"{float(value):.8f},".encode("utf-8"))
        return digest.hexdigest()[:16]
    identity = "|".join(
        [
            str(row.get("pattern_id") or ""),
            str(row.get("source_log_relpath") or row.get("source_log") or ""),
            str(row.get("run_id") or ""),
        ]
    )
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def _prepare_session_embedding_rows(embeddings_payload: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(embeddings_payload, dict):
        return []
    rows = embeddings_payload.get("embeddings") or []
    prepared: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        relpath = str(row.get("source_log_relpath") or "")
        entry = dict(row)
        entry["source_lot"] = _lot_label_from_relpath(relpath)
        entry["embedding_hash"] = _embedding_row_hash(row)
        # Keep full vector in cache for inspect; list API can omit it.
        prepared.append(entry)
    return prepared


def _build_session_similarity_cluster_lookup(
    clustering_payload: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    lookup: Dict[str, str] = {}
    if not isinstance(clustering_payload, dict):
        return lookup
    for row in clustering_payload.get("unit_assignments") or []:
        if not isinstance(row, dict):
            continue
        unit_id = str(row.get("unit_id") or "").strip()
        cluster_id = str(row.get("cluster_id") or "").strip()
        if unit_id and cluster_id:
            lookup[unit_id] = cluster_id
    if lookup:
        return lookup
    for cluster in clustering_payload.get("clusters") or []:
        if not isinstance(cluster, dict):
            continue
        cluster_id = str(cluster.get("cluster_id") or "").strip()
        for row in cluster.get("executions") or []:
            if not isinstance(row, dict):
                continue
            unit_id = str(row.get("unit_id") or "").strip()
            if unit_id and cluster_id:
                lookup[unit_id] = cluster_id
    return lookup


def _session_similarity_meta(lots: List[str]) -> Dict[str, Any]:
    try:
        config = load_similarity_config(
            os.path.join(WORKSPACE_DIR, "config", "similarity.yaml")
        )
        default_top_n = config.default_top_n
        max_top_n = config.max_top_n
        categories = [
            {"key": item.key, "min": item.min_threshold, "label": item.label}
            for item in config.categories_descending
        ]
    except Exception:
        default_top_n = 10
        max_top_n = 100
        categories = []
    return {
        "available": bool(_SESSION_EMBEDDINGS_CACHE),
        "inline": False,
        "unit_count": len(_SESSION_EMBEDDINGS_CACHE),
        "lot_count": len(lots),
        "lots": lots,
        "embedding_version": _SESSION_EMBEDDINGS_META.get("embedding_version"),
        "embedding_dimension": _SESSION_EMBEDDINGS_META.get("embedding_dimension"),
        "similarity_metric": _SESSION_EMBEDDINGS_META.get("similarity_metric") or "cosine",
        "default_top_n": default_top_n,
        "max_top_n": max_top_n,
        "categories": categories,
    }


def _prepare_session_clustering_for_ui(
    clustering_payload: Optional[Dict[str, Any]],
    lots: List[str],
) -> Dict[str, Any]:
    """Shape session clustering for Phase 6 Analysis Session view (never FR-006)."""
    if not isinstance(clustering_payload, dict):
        return {
            "available": False,
            "lots": lots,
            "lot_count": len(lots),
            "clusters": [],
            "charts": {
                "size_distribution": [],
                "lot_contribution": [],
                "execution_distribution": [],
            },
        }
    payload = dict(clustering_payload)
    payload.setdefault("available", True)
    if not payload.get("lots"):
        payload["lots"] = lots
        payload["lot_count"] = len(lots)
    payload.setdefault("clusters", [])
    payload.setdefault(
        "charts",
        {
            "size_distribution": [],
            "lot_contribution": [],
            "execution_distribution": [],
        },
    )
    # Keep parse-workspace lean: unit_assignments/centroids stay on disk for redundancy.
    payload.pop("unit_assignments", None)
    payload.pop("centroids", None)
    return payload


def _prepare_session_redundancy_for_ui(
    redundancy_payload: Optional[Dict[str, Any]],
    lots: List[str],
) -> Dict[str, Any]:
    """Attach redundancy meta only; candidates load via paginated API."""
    if not isinstance(redundancy_payload, dict):
        return {
            "available": False,
            "inline": False,
            "lots": lots,
            "lot_count": len(lots),
            "total_candidates": 0,
            "cluster_ids": [],
            "candidates": [],
        }
    cluster_ids: List[str] = []
    seen_clusters = set()
    for row in redundancy_payload.get("candidates") or []:
        if not isinstance(row, dict):
            continue
        cid = str(row.get("cluster_id") or "")
        if cid and cid not in seen_clusters:
            seen_clusters.add(cid)
            cluster_ids.append(cid)
    cluster_ids.sort()
    meta = {
        "available": redundancy_payload.get("available", True),
        "inline": False,
        "session_hash": redundancy_payload.get("session_hash"),
        "embedding_version": redundancy_payload.get("embedding_version"),
        "embedding_strategy": redundancy_payload.get("embedding_strategy"),
        "cluster_version": redundancy_payload.get("cluster_version"),
        "similarity_threshold": redundancy_payload.get("similarity_threshold"),
        "confidence_source": redundancy_payload.get("confidence_source"),
        "lot_count": redundancy_payload.get("lot_count", len(lots)),
        "lots": redundancy_payload.get("lots") or lots,
        "cluster_ids": cluster_ids,
        "units_total": redundancy_payload.get("units_total"),
        "units_represented": redundancy_payload.get("units_represented"),
        "units_sample_size": redundancy_payload.get("units_sample_size"),
        "units_downsampled": redundancy_payload.get("units_downsampled"),
        "clusters_evaluated": redundancy_payload.get("clusters_evaluated"),
        "total_candidates": redundancy_payload.get("total_candidates", 0),
        "candidates_per_cluster_avg": redundancy_payload.get("candidates_per_cluster_avg"),
        "validation_status": redundancy_payload.get("validation_status"),
        "neighbors_per_unit": redundancy_payload.get("neighbors_per_unit"),
        "candidates_per_cluster_cap": redundancy_payload.get("candidates_per_cluster_cap"),
        "generation_mode": redundancy_payload.get("generation_mode"),
        "validation_checks": redundancy_payload.get("validation_checks") or [],
        "manifest": redundancy_payload.get("manifest") or {},
        "charts": redundancy_payload.get("charts") or {},
    }
    return meta


def _prepare_session_correlation_for_ui(
    payload: Optional[Dict[str, Any]],
    lots: List[str],
) -> Dict[str, Any]:
    """Attach bounded Phase 9 metadata; outcome rows load through the session API."""
    if not isinstance(payload, dict):
        return {
            "available": False,
            "inline": False,
            "outcome_count": 0,
            "lot_count": len(lots),
            "lots": lots,
        }
    return {
        "available": bool(payload.get("available", True)),
        "inline": False,
        "session_hash": payload.get("session_hash"),
        "correlation_version": payload.get("correlation_version"),
        "execution_count": payload.get("execution_count", 0),
        "outcome_count": payload.get("outcome_count", 0),
        "unique_patterns": payload.get("unique_patterns", 0),
        "lot_count": payload.get("lot_count", len(lots)),
        "lots": payload.get("lots") or lots,
        "pass_count": payload.get("pass_count", 0),
        "fail_count": payload.get("fail_count", 0),
        "unknown_count": payload.get("unknown_count", 0),
        "cross_lot_outcomes": payload.get("cross_lot_outcomes", 0),
        "validation_status": payload.get("validation_status"),
    }


def _attach_session_summary(report: Dict[str, Any], session) -> None:
    """Attach Analysis Session payload for UI (additive). Never sets toggle_coverage / FR-004.

    Full execution/embedding/redundancy rows are NOT inlined — cached for paginated session APIs.
    """
    global _SESSION_EXECUTIONS_CACHE, _SESSION_EXECUTIONS_CACHE_HASH
    global _SESSION_EMBEDDINGS_CACHE, _SESSION_EMBEDDINGS_META
    global _SESSION_REDUNDANCY_CACHE, _SESSION_REDUNDANCY_META
    global _SESSION_SIMILARITY_CLUSTER_LOOKUP, _SESSION_SIMILARITY_ENGINE
    global _SESSION_CORRELATION_CACHE, _SESSION_CORRELATION_META
    executions = list(session.executions or [])
    _SESSION_EXECUTIONS_CACHE = executions
    _SESSION_EXECUTIONS_CACHE_HASH = session.manifest.get("session_hash")
    coverage_kpis = _build_session_coverage_kpis(executions)

    emb_payload = session.embeddings if isinstance(session.embeddings, dict) else None
    _SESSION_EMBEDDINGS_CACHE = _prepare_session_embedding_rows(emb_payload)
    lots = []
    seen_lots = set()
    for log_name in session.manifest.get("input_ate_logs") or []:
        lot = _lot_label_from_relpath(log_name)
        if lot not in seen_lots:
            seen_lots.add(lot)
            lots.append(lot)
    _SESSION_EMBEDDINGS_META = {
        "available": emb_payload is not None,
        "patterns_embedded": (emb_payload or {}).get("patterns_embedded", len(_SESSION_EMBEDDINGS_CACHE)),
        "patterns_skipped": (emb_payload or {}).get("patterns_skipped", 0),
        "embedding_dimension": (emb_payload or {}).get("embedding_dimension"),
        "embedding_version": (emb_payload or {}).get("embedding_version"),
        "algorithm": (emb_payload or {}).get("algorithm"),
        "similarity_metric": (emb_payload or {}).get("similarity_metric"),
        "embedding_strategy": (emb_payload or {}).get("embedding_strategy"),
        "lot_count": len(lots),
        "lots": lots,
        "execution_count": session.manifest.get("execution_count"),
        "execution_record_count": session.summary.get("execution_record_count"),
        "unique_patterns": len({str(r.get("pattern_id")) for r in _SESSION_EMBEDDINGS_CACHE}),
    }

    red_payload = session.redundancy if isinstance(session.redundancy, dict) else None
    _SESSION_REDUNDANCY_CACHE = list((red_payload or {}).get("candidates") or [])
    _SESSION_REDUNDANCY_META = _prepare_session_redundancy_for_ui(red_payload, lots)
    _SESSION_SIMILARITY_CLUSTER_LOOKUP = _build_session_similarity_cluster_lookup(
        session.clustering
    )
    _SESSION_SIMILARITY_ENGINE = None
    corr_payload = session.correlation if isinstance(session.correlation, dict) else None
    _SESSION_CORRELATION_CACHE = list((corr_payload or {}).get("outcomes") or [])
    _SESSION_CORRELATION_META = _prepare_session_correlation_for_ui(corr_payload, lots)

    report["analysis_session"] = {
        "generated_by": session.manifest.get("generated_by"),
        "session_hash": session.manifest.get("session_hash"),
        "stil_file": session.manifest.get("stil_file"),
        "input_ate_logs": session.manifest.get("input_ate_logs"),
        "execution_count": session.manifest.get("execution_count"),
        "generated_timestamp": session.manifest.get("generated_timestamp"),
        "execution_record_count": session.summary.get("execution_record_count"),
        "summary": session.summary,
        # Empty list keeps Array.isArray checks working; rows load via paginated API.
        "executions": [],
        "executions_inline": False,
        "executions_available": True,
        "coverage_kpis": coverage_kpis,
        "session_embeddings": {
            "available": _SESSION_EMBEDDINGS_META["available"],
            "inline": False,
            **{k: v for k, v in _SESSION_EMBEDDINGS_META.items() if k != "available"},
        },
        "session_clustering": _prepare_session_clustering_for_ui(session.clustering, lots),
        "session_redundancy": dict(_SESSION_REDUNDANCY_META),
        "session_similarity": _session_similarity_meta(lots),
        "session_correlation": dict(_SESSION_CORRELATION_META),
        "artifacts": {
            "manifest": True,
            "executions": True,
            "summary": True,
            "scan_vectors": session.scan_vectors is not None,
            "embeddings": session.embeddings is not None,
            "clustering": session.clustering is not None,
            "redundancy": session.redundancy is not None,
            "correlation": session.correlation is not None,
            "failure_predictions_by_lot": os.path.isfile(
                os.path.join(
                    OUTPUT_DIR, "PA-Analysis-Session_failure_predictions_by_lot.json"
                )
            ),
            "failure_predictions": os.path.isfile(
                os.path.join(OUTPUT_DIR, "PA-Analysis-Session_failure_predictions.json")
            ),
            "anomaly_scores_by_lot": os.path.isfile(
                os.path.join(
                    OUTPUT_DIR, "PA-Analysis-Session_anomaly_scores_by_lot.json"
                )
            ),
            "anomaly_scores": os.path.isfile(
                os.path.join(OUTPUT_DIR, "PA-Analysis-Session_anomaly_scores.json")
            ),
            "root_cause_rankings_by_lot": os.path.isfile(
                os.path.join(
                    OUTPUT_DIR, "PA-Analysis-Session_root_cause_rankings_by_lot.json"
                )
            ),
            "root_cause_rankings": os.path.isfile(
                os.path.join(OUTPUT_DIR, "PA-Analysis-Session_root_cause_rankings.json")
            ),
            "pattern_recommendations_by_lot": os.path.isfile(
                os.path.join(
                    OUTPUT_DIR, "PA-Analysis-Session_pattern_recommendations_by_lot.json"
                )
            ),
            "pattern_recommendations": os.path.isfile(
                os.path.join(OUTPUT_DIR, "PA-Analysis-Session_pattern_recommendations.json")
            ),
        },
    }


def _load_session_executions_cache() -> List[Dict[str, Any]]:
    global _SESSION_EXECUTIONS_CACHE, _SESSION_EXECUTIONS_CACHE_HASH
    if _SESSION_EXECUTIONS_CACHE:
        return _SESSION_EXECUTIONS_CACHE
    path = os.path.join(OUTPUT_DIR, SESSION_EXECUTIONS_JSON)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        rows = payload.get("executions") if isinstance(payload, dict) else None
        if isinstance(rows, list):
            _SESSION_EXECUTIONS_CACHE = rows
            return _SESSION_EXECUTIONS_CACHE
    except Exception:
        return []
    return []


def _session_embeddings_meta_incomplete(meta: Dict[str, Any]) -> bool:
    if not meta:
        return True
    return meta.get("embedding_dimension") is None or meta.get("embedding_version") is None


def _build_session_embeddings_meta_from_payload(
    payload: Dict[str, Any],
    rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    lots = sorted(
        {
            str(row.get("source_lot") or _lot_label_from_relpath(
                str(row.get("source_log_relpath") or row.get("source_log") or "")
            ))
            for row in rows
        }
    )
    return {
        "available": True,
        "patterns_embedded": payload.get("patterns_embedded", len(rows)),
        "patterns_skipped": payload.get("patterns_skipped", 0),
        "embedding_dimension": payload.get("embedding_dimension"),
        "embedding_version": payload.get("embedding_version"),
        "algorithm": payload.get("algorithm"),
        "similarity_metric": payload.get("similarity_metric"),
        "embedding_strategy": payload.get("embedding_strategy"),
        "lot_count": len(lots),
        "lots": lots,
        "unique_patterns": len({str(r.get("pattern_id")) for r in rows}),
    }


def _load_session_embeddings_cache() -> List[Dict[str, Any]]:
    global _SESSION_EMBEDDINGS_CACHE, _SESSION_EMBEDDINGS_META
    if _SESSION_EMBEDDINGS_CACHE and not _session_embeddings_meta_incomplete(_SESSION_EMBEDDINGS_META):
        return _SESSION_EMBEDDINGS_CACHE
    path = os.path.join(OUTPUT_DIR, SESSION_EMBEDDINGS_JSON)
    if not os.path.exists(path):
        return _SESSION_EMBEDDINGS_CACHE or []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            if not _SESSION_EMBEDDINGS_CACHE:
                _SESSION_EMBEDDINGS_CACHE = _prepare_session_embedding_rows(payload)
            rebuilt_meta = _session_embeddings_meta_incomplete(_SESSION_EMBEDDINGS_META)
            if rebuilt_meta:
                _SESSION_EMBEDDINGS_META = _build_session_embeddings_meta_from_payload(
                    payload,
                    _SESSION_EMBEDDINGS_CACHE,
                )
            return _SESSION_EMBEDDINGS_CACHE
    except Exception as exc:
        return _SESSION_EMBEDDINGS_CACHE or []
    return _SESSION_EMBEDDINGS_CACHE or []


@app.get("/api/analysis-session/executions")
def get_analysis_session_executions(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
):
    """Paginated session executions for UI. Avoids inlining millions of rows in parse-workspace."""
    rows = _load_session_executions_cache()
    query = (q or "").strip().lower()
    if query:
        filtered = []
        for row in rows:
            blob = " ".join(
                str(row.get(key) or "")
                for key in (
                    "pattern_id",
                    "scan_chain_id",
                    "source_log",
                    "source_log_relpath",
                    "run_id",
                    "latest_result",
                )
            ).lower()
            if query in blob:
                filtered.append(row)
        rows = filtered
    total = len(rows)
    page = rows[offset : offset + limit]
    return {
        "session_hash": _SESSION_EXECUTIONS_CACHE_HASH,
        "total": total,
        "offset": offset,
        "limit": limit,
        "executions": page,
    }


@app.get("/api/analysis-session/embeddings")
def get_analysis_session_embeddings(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    include_vector: bool = Query(False),
):
    """Paginated session embeddings for Phase 5 Analysis Session view (not PA-FR-005)."""
    rows = _load_session_embeddings_cache()
    query = (q or "").strip().lower()
    if query:
        filtered = []
        for row in rows:
            blob = " ".join(
                str(row.get(key) or "")
                for key in (
                    "pattern_id",
                    "source_lot",
                    "source_log",
                    "source_log_relpath",
                    "run_id",
                    "embedding_hash",
                    "embedding_version",
                    "feature_version",
                )
            ).lower()
            if query in blob:
                filtered.append(row)
        rows = filtered
    total = len(rows)
    page_src = rows[offset : offset + limit]
    page = []
    for row in page_src:
        item = {
            "pattern_id": row.get("pattern_id"),
            "source_lot": row.get("source_lot"),
            "source_log": row.get("source_log"),
            "source_log_relpath": row.get("source_log_relpath"),
            "run_id": row.get("run_id"),
            "embedding_hash": row.get("embedding_hash"),
            "embedding_version": row.get("embedding_version") or _SESSION_EMBEDDINGS_META.get("embedding_version"),
            "feature_version": row.get("feature_version"),
            "similarity_metric": _SESSION_EMBEDDINGS_META.get("similarity_metric"),
            "algorithm": _SESSION_EMBEDDINGS_META.get("algorithm"),
            "embedding_dimension": _SESSION_EMBEDDINGS_META.get("embedding_dimension"),
            "created_timestamp": row.get("created_timestamp"),
            "source_file": row.get("source_file"),
            "embedding_status": "OK" if row.get("embedding") else "MISSING",
        }
        if include_vector:
            item["embedding"] = row.get("embedding")
        page.append(item)
    return {
        "session_hash": _SESSION_EXECUTIONS_CACHE_HASH,
        "meta": _SESSION_EMBEDDINGS_META,
        "total": total,
        "offset": offset,
        "limit": limit,
        "embeddings": page,
    }


def _load_session_similarity_cluster_lookup() -> Dict[str, str]:
    global _SESSION_SIMILARITY_CLUSTER_LOOKUP
    if _SESSION_SIMILARITY_CLUSTER_LOOKUP:
        return _SESSION_SIMILARITY_CLUSTER_LOOKUP
    path = os.path.join(OUTPUT_DIR, SESSION_CLUSTERING_JSON)
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        _SESSION_SIMILARITY_CLUSTER_LOOKUP = (
            _build_session_similarity_cluster_lookup(payload)
        )
    except Exception:
        return {}
    return _SESSION_SIMILARITY_CLUSTER_LOOKUP


def _build_session_similarity_engine() -> SessionSimilarityEngine:
    global _SESSION_SIMILARITY_ENGINE
    if _SESSION_SIMILARITY_ENGINE is not None:
        return _SESSION_SIMILARITY_ENGINE
    rows = _load_session_embeddings_cache()
    if not rows:
        raise SimilarityAbortError(
            "Analysis Session embeddings are not available. Run a multi-log analysis first."
        )
    _SESSION_SIMILARITY_ENGINE = SessionSimilarityEngine.from_rows(
        rows=rows,
        workspace_dir=WORKSPACE_DIR,
        embedding_version=str(
            _SESSION_EMBEDDINGS_META.get("embedding_version") or "1.0"
        ),
        cluster_by_unit=_load_session_similarity_cluster_lookup(),
    )
    return _SESSION_SIMILARITY_ENGINE


@app.get("/api/analysis-session/similarity/options")
def get_analysis_session_similarity_options(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: str = Query(""),
    lot: str = Query(""),
    cluster: str = Query(""),
):
    """Searchable execution-unit selector; vectors are never returned."""
    rows = _load_session_embeddings_cache()
    cluster_lookup = _load_session_similarity_cluster_lookup()
    query = (q or "").strip().lower()
    lot_filter = (lot or "").strip()
    cluster_filter = (cluster or "").strip()
    options = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("embedding"):
            continue
        uid = session_unit_id(row)
        row_lot = source_lot(row)
        cluster_id = cluster_lookup.get(uid)
        if lot_filter and lot_filter != "All" and row_lot != lot_filter:
            continue
        if cluster_filter and cluster_filter != "All" and cluster_id != cluster_filter:
            continue
        label = (
            f"{row.get('pattern_id') or ''} — {row_lot} / "
            f"{row.get('source_log_relpath') or row.get('source_log') or ''}"
        )
        if query:
            blob = " ".join(
                [
                    uid,
                    label,
                    str(row.get("run_id") or ""),
                    str(cluster_id or ""),
                ]
            ).lower()
            if query not in blob:
                continue
        options.append(
            {
                "unit_id": uid,
                "label": label,
                "pattern_id": row.get("pattern_id"),
                "source_lot": row_lot,
                "source_log": row.get("source_log"),
                "source_log_relpath": row.get("source_log_relpath"),
                "run_id": row.get("run_id"),
                "cluster_id": cluster_id,
                "embedding_version": (
                    row.get("embedding_version")
                    or row.get("feature_version")
                    or _SESSION_EMBEDDINGS_META.get("embedding_version")
                ),
            }
        )
    options.sort(key=lambda item: str(item["unit_id"]))
    total = len(options)
    return {
        "session_hash": _SESSION_EXECUTIONS_CACHE_HASH,
        "meta": _session_similarity_meta(
            list(_SESSION_EMBEDDINGS_META.get("lots") or [])
        ),
        "total": total,
        "offset": offset,
        "limit": limit,
        "options": options[offset : offset + limit],
    }


@app.post("/api/analysis-session/similarity/pair")
def analysis_session_similarity_pair(req: SessionSimilarityPairRequest):
    try:
        return _build_session_similarity_engine().compute_pair(
            req.unit_a, req.unit_b
        )
    except SimilarityValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SimilarityAbortError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/analysis-session/similarity/top-n")
def analysis_session_similarity_top_n(req: SessionSimilarityTopNRequest):
    try:
        return _build_session_similarity_engine().compute_top_n(
            req.reference_unit, req.top_n
        )
    except SimilarityValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SimilarityAbortError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _load_session_correlation_cache() -> List[Dict[str, Any]]:
    global _SESSION_CORRELATION_CACHE, _SESSION_CORRELATION_META
    if _SESSION_CORRELATION_CACHE:
        return _SESSION_CORRELATION_CACHE
    path = os.path.join(OUTPUT_DIR, SESSION_CORRELATION_JSON)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            _SESSION_CORRELATION_CACHE = list(payload.get("outcomes") or [])
            if not _SESSION_CORRELATION_META:
                _SESSION_CORRELATION_META = _prepare_session_correlation_for_ui(
                    payload, list(payload.get("lots") or [])
                )
    except Exception:
        return []
    return _SESSION_CORRELATION_CACHE


@app.get("/api/analysis-session/correlation/analytics")
def get_analysis_session_correlation_analytics(
    top_n: int = Query(10, ge=1, le=100),
):
    """Bounded Phase 9 dashboard aggregates; histories remain server-side."""
    rows = _load_session_correlation_cache()
    return {
        "session_hash": _SESSION_CORRELATION_META.get("session_hash")
        or _SESSION_EXECUTIONS_CACHE_HASH,
        "meta": _SESSION_CORRELATION_META,
        "analytics": build_session_correlation_analytics(
            rows, top_n=top_n, robustness_cfg=_ROBUSTNESS_CFG
        ),
    }


@app.get("/api/analysis-session/correlation")
def get_analysis_session_correlation(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    latest_result: str = Query(""),
    lot: str = Query(""),
    cross_lot: str = Query(""),
):
    """Paginated session-native Phase 9 outcomes with execution provenance."""
    rows = _load_session_correlation_cache()
    query = (q or "").strip().lower()
    result_filter = (latest_result or "").strip().upper()
    lot_filter = (lot or "").strip()
    cross_filter = (cross_lot or "").strip().lower()
    filtered = []
    for row in rows:
        if result_filter and result_filter != "ALL":
            if str(row.get("latest_result") or "").upper() != result_filter:
                continue
        if lot_filter and lot_filter != "All":
            if lot_filter not in list(row.get("source_lots") or []):
                continue
        if cross_filter in ("yes", "true") and not bool(row.get("cross_lot")):
            continue
        if cross_filter in ("no", "false") and bool(row.get("cross_lot")):
            continue
        if query:
            blob = " ".join(
                [
                    str(row.get("pattern_id") or ""),
                    str(row.get("scan_chain_id") or ""),
                    str(row.get("latest_result") or ""),
                    " ".join(str(item) for item in row.get("source_lots") or []),
                    " ".join(
                        str(item.get("source_log_relpath") or item.get("source_log") or "")
                        for item in row.get("history") or []
                    ),
                ]
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)
    filtered.sort(
        key=lambda row: (
            str(row.get("pattern_id") or ""),
            str(row.get("scan_chain_id") or ""),
        )
    )
    total = len(filtered)
    return {
        "session_hash": _SESSION_CORRELATION_META.get("session_hash")
        or _SESSION_EXECUTIONS_CACHE_HASH,
        "meta": _SESSION_CORRELATION_META,
        "total": total,
        "offset": offset,
        "limit": limit,
        "outcomes": filtered[offset : offset + limit],
    }


def _load_session_redundancy_cache() -> List[Dict[str, Any]]:
    global _SESSION_REDUNDANCY_CACHE, _SESSION_REDUNDANCY_META
    if _SESSION_REDUNDANCY_CACHE:
        return _SESSION_REDUNDANCY_CACHE
    path = os.path.join(OUTPUT_DIR, SESSION_REDUNDANCY_JSON)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            _SESSION_REDUNDANCY_CACHE = list(payload.get("candidates") or [])
            if not _SESSION_REDUNDANCY_META:
                _SESSION_REDUNDANCY_META = _prepare_session_redundancy_for_ui(payload, [])
            return _SESSION_REDUNDANCY_CACHE
    except Exception:
        return []
    return []


@app.get("/api/analysis-session/anomaly-scores-by-lot")
def get_analysis_session_anomaly_scores_by_lot(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    is_anomaly: str = Query(""),
    lot: str = Query(""),
):
    """Paginated PA-ML-002-LOT advisory anomaly scores (pattern × LOT)."""
    path = os.path.join(OUTPUT_DIR, "PA-Analysis-Session_anomaly_scores_by_lot.json")
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read LOT anomaly scores: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Invalid LOT anomaly scores payload.")

    rows = [row for row in (payload.get("scores") or []) if isinstance(row, dict)]
    query = (q or "").strip().lower()
    anomaly_f = (is_anomaly or "").strip()
    lot_f = (lot or "").strip()
    filtered = []
    for row in rows:
        if anomaly_f and anomaly_f != "All":
            try:
                if int(row.get("is_anomaly") or 0) != int(anomaly_f):
                    continue
            except (TypeError, ValueError):
                continue
        if lot_f and lot_f != "All" and str(row.get("source_lot") or "") != lot_f:
            continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in ("unit_id", "pattern_id", "source_lot")
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "feature_schema_version": payload.get("feature_schema_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "grain": payload.get("grain"),
            "score_count": payload.get("score_count"),
            "anomaly_count": payload.get("anomaly_count"),
        },
    }


@app.get("/api/analysis-session/anomaly-scores")
def get_analysis_session_anomaly_scores(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    is_anomaly: str = Query(""),
):
    """Paginated PA-ML-002 advisory anomaly scores (pattern × log)."""
    path = os.path.join(OUTPUT_DIR, "PA-Analysis-Session_anomaly_scores.json")
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read anomaly scores: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Invalid anomaly scores payload.")

    rows = [row for row in (payload.get("scores") or []) if isinstance(row, dict)]
    query = (q or "").strip().lower()
    anomaly_f = (is_anomaly or "").strip()
    filtered = []
    for row in rows:
        if anomaly_f and anomaly_f != "All":
            try:
                if int(row.get("is_anomaly") or 0) != int(anomaly_f):
                    continue
            except (TypeError, ValueError):
                continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in ("unit_id", "pattern_id", "source_log", "source_lot")
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "feature_schema_version": payload.get("feature_schema_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "grain": payload.get("grain"),
            "score_count": payload.get("score_count"),
            "anomaly_count": payload.get("anomaly_count"),
        },
    }


@app.get("/api/analysis-session/root-cause-rankings-by-lot")
def get_analysis_session_root_cause_rankings_by_lot(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    result: str = Query(""),
    lot: str = Query(""),
):
    """Paginated PA-ML-003-LOT advisory root-cause rankings (pattern × LOT)."""
    path = os.path.join(
        OUTPUT_DIR, "PA-Analysis-Session_root_cause_rankings_by_lot.json"
    )
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read LOT root-cause rankings: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500, detail="Invalid LOT root-cause rankings payload."
        )

    rows = [row for row in (payload.get("rankings") or []) if isinstance(row, dict)]
    query = (q or "").strip().lower()
    result_f = (result or "").strip().upper()
    lot_f = (lot or "").strip()
    filtered = []
    for row in rows:
        if result_f and result_f != "ALL":
            if str(row.get("actual_result") or "").upper() != result_f:
                continue
        if lot_f and lot_f != "All" and str(row.get("source_lot") or "") != lot_f:
            continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in (
                    "unit_id",
                    "pattern_id",
                    "source_lot",
                    "scan_chain_id",
                )
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "feature_schema_version": payload.get("feature_schema_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "grain": payload.get("grain"),
            "ranking_count": payload.get("ranking_count"),
            "fail_count": payload.get("fail_count"),
            "disclaimer": payload.get("disclaimer"),
        },
    }


@app.get("/api/analysis-session/root-cause-rankings")
def get_analysis_session_root_cause_rankings(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    result: str = Query(""),
):
    """Paginated PA-ML-003 advisory root-cause rankings (pattern × log)."""
    path = os.path.join(OUTPUT_DIR, "PA-Analysis-Session_root_cause_rankings.json")
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read root-cause rankings: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500, detail="Invalid root-cause rankings payload."
        )

    rows = [row for row in (payload.get("rankings") or []) if isinstance(row, dict)]
    query = (q or "").strip().lower()
    result_f = (result or "").strip().upper()
    filtered = []
    for row in rows:
        if result_f and result_f != "ALL":
            if str(row.get("actual_result") or "").upper() != result_f:
                continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in (
                    "unit_id",
                    "pattern_id",
                    "source_log",
                    "scan_chain_id",
                )
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "feature_schema_version": payload.get("feature_schema_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "grain": payload.get("grain"),
            "ranking_count": payload.get("ranking_count"),
            "fail_count": payload.get("fail_count"),
            "disclaimer": payload.get("disclaimer"),
        },
    }


@app.get("/api/analysis-session/pattern-recommendations-by-lot")
def get_analysis_session_pattern_recommendations_by_lot(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    tier: str = Query(""),
    action: str = Query(""),
    lot: str = Query(""),
):
    """Paginated PA-ML-004-LOT advisory pattern recommendations (pattern × LOT)."""
    path = os.path.join(
        OUTPUT_DIR, "PA-Analysis-Session_pattern_recommendations_by_lot.json"
    )
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read LOT pattern recommendations: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500, detail="Invalid LOT pattern recommendations payload."
        )

    rows = [
        row for row in (payload.get("recommendations") or []) if isinstance(row, dict)
    ]
    query = (q or "").strip().lower()
    tier_f = (tier or "").strip().upper()
    action_f = (action or "").strip().upper()
    lot_f = (lot or "").strip()
    filtered = []
    for row in rows:
        if tier_f and tier_f != "ALL" and str(row.get("priority_tier") or "").upper() != tier_f:
            continue
        if action_f and action_f != "ALL":
            if str(row.get("recommended_action") or "").upper() != action_f:
                continue
        if lot_f and lot_f != "All" and str(row.get("source_lot") or "") != lot_f:
            continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in (
                    "unit_id",
                    "pattern_id",
                    "source_lot",
                    "scan_chain_id",
                    "recommended_action",
                )
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "policy_version": payload.get("policy_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "grain": payload.get("grain"),
            "recommendation_count": payload.get("recommendation_count"),
            "high_priority_count": payload.get("high_priority_count"),
            "disclaimer": payload.get("disclaimer"),
        },
    }


@app.get("/api/analysis-session/pattern-recommendations")
def get_analysis_session_pattern_recommendations(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    tier: str = Query(""),
    action: str = Query(""),
):
    """Paginated PA-ML-004 advisory pattern recommendations (pattern × log)."""
    path = os.path.join(OUTPUT_DIR, "PA-Analysis-Session_pattern_recommendations.json")
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read pattern recommendations: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500, detail="Invalid pattern recommendations payload."
        )

    rows = [
        row for row in (payload.get("recommendations") or []) if isinstance(row, dict)
    ]
    query = (q or "").strip().lower()
    tier_f = (tier or "").strip().upper()
    action_f = (action or "").strip().upper()
    filtered = []
    for row in rows:
        if tier_f and tier_f != "ALL" and str(row.get("priority_tier") or "").upper() != tier_f:
            continue
        if action_f and action_f != "ALL":
            if str(row.get("recommended_action") or "").upper() != action_f:
                continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in (
                    "unit_id",
                    "pattern_id",
                    "source_log",
                    "scan_chain_id",
                    "recommended_action",
                )
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "policy_version": payload.get("policy_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "grain": payload.get("grain"),
            "recommendation_count": payload.get("recommendation_count"),
            "high_priority_count": payload.get("high_priority_count"),
            "disclaimer": payload.get("disclaimer"),
        },
    }


@app.get("/api/analysis-session/failure-predictions-by-lot")
def get_analysis_session_failure_predictions_by_lot(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    label_pred: str = Query(""),
    lot: str = Query(""),
):
    """Paginated PA-ML-001-LOT advisory failure predictions (pattern × LOT)."""
    path = os.path.join(
        OUTPUT_DIR, "PA-Analysis-Session_failure_predictions_by_lot.json"
    )
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read LOT failure predictions: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=500, detail="Invalid LOT failure predictions payload."
        )

    rows = [
        row for row in (payload.get("predictions") or []) if isinstance(row, dict)
    ]
    query = (q or "").strip().lower()
    label_f = (label_pred or "").strip()
    lot_f = (lot or "").strip()
    filtered = []
    for row in rows:
        if label_f and label_f != "All":
            try:
                if int(row.get("label_pred") or 0) != int(label_f):
                    continue
            except (TypeError, ValueError):
                continue
        if lot_f and lot_f != "All" and str(row.get("source_lot") or "") != lot_f:
            continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in ("unit_id", "pattern_id", "source_lot")
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "feature_schema_version": payload.get("feature_schema_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "grain": payload.get("grain"),
            "prediction_count": payload.get("prediction_count"),
        },
    }


@app.get("/api/analysis-session/failure-predictions")
def get_analysis_session_failure_predictions(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    label_pred: str = Query(""),
):
    """Paginated PA-ML-001 advisory failure predictions (Layer 3 only)."""
    path = os.path.join(OUTPUT_DIR, "PA-Analysis-Session_failure_predictions.json")
    if not os.path.isfile(path):
        return {
            "available": False,
            "total": 0,
            "offset": offset,
            "limit": limit,
            "rows": [],
            "meta": {},
        }
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to read failure predictions: {exc}",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="Invalid failure predictions payload.")

    rows = [
        row for row in (payload.get("predictions") or []) if isinstance(row, dict)
    ]
    query = (q or "").strip().lower()
    label_f = (label_pred or "").strip()
    filtered = []
    for row in rows:
        if label_f and label_f != "All":
            try:
                if int(row.get("label_pred") or 0) != int(label_f):
                    continue
            except (TypeError, ValueError):
                continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in ("unit_id", "pattern_id", "source_log", "source_lot")
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "available": True,
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": page,
        "meta": {
            "generated_by": payload.get("generated_by"),
            "model_version": payload.get("model_version"),
            "feature_schema_version": payload.get("feature_schema_version"),
            "session_hash": payload.get("session_hash"),
            "status": payload.get("status"),
            "prediction_count": payload.get("prediction_count"),
        },
    }


@app.get("/api/analysis-session/redundancy")
def get_analysis_session_redundancy(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    q: str = Query(""),
    confidence: str = Query(""),
    review_status: str = Query(""),
    label: str = Query(""),
    cluster: str = Query(""),
    lot: str = Query(""),
):
    """Paginated session redundancy candidates for Phase 7 Analysis Session view."""
    rows = _load_session_redundancy_cache()
    query = (q or "").strip().lower()
    confidence_f = (confidence or "").strip()
    review_f = (review_status or "").strip()
    label_f = (label or "").strip()
    cluster_f = (cluster or "").strip()
    lot_f = (lot or "").strip()

    def _confidence_band(score: float) -> str:
        if score >= 0.45:
            return "Very High"
        if score >= 0.40:
            return "High"
        if score >= 0.30:
            return "Medium"
        return "Low"

    filtered = []
    for row in rows:
        if confidence_f and confidence_f != "All":
            if _confidence_band(float(row.get("confidence_score") or 0)) != confidence_f:
                continue
        if review_f and review_f != "All" and str(row.get("review_status") or "") != review_f:
            continue
        if label_f and label_f != "All" and str(row.get("label") or "") != label_f:
            continue
        if cluster_f and cluster_f != "All" and str(row.get("cluster_id") or "") != cluster_f:
            continue
        if lot_f and lot_f != "All":
            lots_hit = {
                str(row.get("source_lot_a") or ""),
                str(row.get("source_lot_b") or ""),
            }
            if lot_f not in lots_hit:
                continue
        if query:
            blob = " ".join(
                str(row.get(key) or "")
                for key in (
                    "pattern_a",
                    "pattern_b",
                    "unit_a",
                    "unit_b",
                    "cluster_id",
                    "source_lot_a",
                    "source_lot_b",
                    "source_log_a",
                    "source_log_b",
                    "review_status",
                    "label",
                )
            ).lower()
            if query not in blob:
                continue
        filtered.append(row)

    total = len(filtered)
    page = filtered[offset : offset + limit]
    return {
        "session_hash": _SESSION_EXECUTIONS_CACHE_HASH,
        "meta": _SESSION_REDUNDANCY_META,
        "total": total,
        "offset": offset,
        "limit": limit,
        "candidates": page,
    }


def _run_multi_log_session_path(report: Dict[str, Any], selected_logs: list[str]) -> None:
    """
    Multi-log Analysis Session path: write PA-Analysis-Session_* only.
    Does not write PA-FR-004 / PA-FR-005 artifacts and does not invoke FR-005–008.
    """
    resolved_logs: list[str] = []
    for log_name in selected_logs:
        candidate = (
            log_name
            if os.path.isabs(log_name)
            else os.path.join(WORKSPACE_DIR, log_name)
        )
        if not os.path.exists(candidate):
            alt = os.path.join(ATE_UPLOAD_DIR, os.path.basename(log_name))
            if os.path.exists(alt):
                candidate = alt
            else:
                raise HTTPException(status_code=404, detail=f"ATE log not found: {log_name}")
        _enforce_ate_log_size_limit(candidate)
        resolved_logs.append(candidate)

    try:
        write_requirement_outputs(report)
    except Exception as exc:
        print(f"Error writing requirement outputs: {str(exc)}")

    try:
        session = run_analysis_session_pipeline(
            workspace_dir=WORKSPACE_DIR,
            output_dir=OUTPUT_DIR,
            stil_file=report.get("file_name") or "",
            requested_log_paths=resolved_logs,
            metadata_path=os.path.join(OUTPUT_DIR, "PA-FR-003_metadata_metrics.json"),
        )
    except SessionPathError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis Session pipeline failed: {exc}",
        ) from exc

    _attach_session_summary(report, session)
    # C2: adapter infrastructure only — projection deferred; engines not invoked.
    report["session_downstream"] = prepare_session_downstream(OUTPUT_DIR, WORKSPACE_DIR)


def _execute_parse_workspace(req: WorkspaceFileRequest) -> Dict[str, Any]:
    """
    Shared Validate execution path (engineering unchanged).

    Used by POST /api/parse-workspace and PA-UX-003 analysis jobs.
    """
    global _SESSION_EXECUTIONS_CACHE, _SESSION_EXECUTIONS_CACHE_HASH
    global _SESSION_EMBEDDINGS_CACHE, _SESSION_EMBEDDINGS_META
    global _SESSION_REDUNDANCY_CACHE, _SESSION_REDUNDANCY_META
    global _SESSION_SIMILARITY_CLUSTER_LOOKUP, _SESSION_SIMILARITY_ENGINE
    global _SESSION_CORRELATION_CACHE, _SESSION_CORRELATION_META
    file_path = os.path.join(WORKSPACE_DIR, req.filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{req.filename}' not found in workspace")

    config = load_config()
    max_gb = config.get("max_file_size_gb", 10.0)

    start_time = time.time()
    parser = STILParser()
    report = parser.parse(
        file_path,
        max_size_gb=max_gb,
        waveform_table_mode=_ROBUSTNESS_CFG.stil_validation.waveform_table_mode,
    )
    duration = time.time() - start_time
    report["parsing_duration_seconds"] = round(duration, 3)

    selected_logs = resolve_selected_ate_logs(req.ate_log_filename, req.ate_log_filenames)
    # Auto-ingest: when caller omitted ATE selection and multiple logs exist, use ALL
    # discovered logs for Analysis Session instead of failing with a selection error.
    if not selected_logs:
        all_abs = _collect_workspace_ate_logs()
        if len(all_abs) >= 2:
            selected_logs = [
                os.path.relpath(p, WORKSPACE_DIR).replace("\\", "/")
                for p in all_abs
            ]
        elif len(all_abs) == 1:
            selected_logs = [
                os.path.relpath(all_abs[0], WORKSPACE_DIR).replace("\\", "/")
            ]
    use_session = should_use_session_path(selected_logs)
    if use_session:
        _run_multi_log_session_path(report, selected_logs)
        return report

    # Legacy single-log path (byte-compatible with prior behavior).
    _SESSION_EXECUTIONS_CACHE = []
    _SESSION_EXECUTIONS_CACHE_HASH = None
    _SESSION_EMBEDDINGS_CACHE = []
    _SESSION_EMBEDDINGS_META = {}
    _SESSION_REDUNDANCY_CACHE = []
    _SESSION_REDUNDANCY_META = {}
    _SESSION_SIMILARITY_CLUSTER_LOOKUP = {}
    _SESSION_SIMILARITY_ENGINE = None
    _SESSION_CORRELATION_CACHE = []
    _SESSION_CORRELATION_META = {}
    _clear_session_artifacts(OUTPUT_DIR)
    ate_manual = selected_logs[0] if selected_logs else req.ate_log_filename
    try:
        ate_log_path = calculate_and_attach_coverage(report, ate_manual)
    except HTTPException:
        raise
    except Exception as exc:
        raise

    # Export outputs to workspace output folder
    try:
        write_requirement_outputs(report)
    except Exception as e:
        # Log to stderr but do not block response
        print(f"Error writing requirement outputs: {str(e)}")

    try:
        embedding_summary = run_pa_fr_005_extensions(report, ate_log_path)
    except Exception as exc:
        raise

    if embedding_summary:
        report["pattern_embeddings"] = embedding_summary
        validation_summary = run_pa_fr_005_validation()
        if validation_summary:
            report["embedding_validation"] = validation_summary

        try:
            clustering_summary = run_pa_fr_006_extensions(report)
        except Exception as exc:
            raise

        if clustering_summary:
            report["pattern_clustering"] = clustering_summary
            redundancy_summary = run_pa_fr_007_extensions(report)
            if redundancy_summary:
                report["pattern_redundancy"] = redundancy_summary

    return report


@app.post("/api/parse-workspace")
def parse_workspace_file(req: WorkspaceFileRequest):
    try:
        return _execute_parse_workspace(req)
    except HTTPException as exc:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"parse-workspace failed: {exc}") from exc


def _safe_job_error_detail(exc: BaseException) -> str:
    if isinstance(exc, HTTPException):
        detail = exc.detail
        if isinstance(detail, str) and detail.strip():
            return detail.strip()[:200]
        return "Validation failed"
    # Short safe message — no traceback for UI
    text = str(exc or "").strip()
    if text:
        return text[:200]
    return "Validation failed"


def _run_analysis_job(job_id: str, req: WorkspaceFileRequest) -> None:
    with progress_job_context(job_id):
        progress_manager.mark_running(job_id)
        try:
            report = _execute_parse_workspace(req)
            progress_manager.complete(job_id, report)
        except BaseException as exc:
            snap = progress_manager.snapshot(job_id) or {}
            phase = snap.get("current_phase") or "ingestion"
            progress_manager.fail(job_id, _safe_job_error_detail(exc), phase=phase)


@app.post("/api/analysis/start")
def start_analysis_job(req: WorkspaceFileRequest):
    """PA-UX-003 — start Validate as a background job; returns job_id only."""
    weights = load_phase_weights_from_perf_trace(OUTPUT_DIR)
    job_id = progress_manager.create_job(phase_weights=weights)
    _ANALYSIS_JOB_EXECUTOR.submit(_run_analysis_job, job_id, req)
    return {"job_id": job_id}


@app.get("/api/analysis/progress/{job_id}")
def get_analysis_job_progress(job_id: str):
    snap = progress_manager.snapshot(job_id)
    if snap is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    return snap


@app.get("/api/analysis/result/{job_id}")
def get_analysis_job_result(job_id: str):
    state = progress_manager.get_result(job_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Analysis job not found.")
    if state.status == "running" or state.status == "queued":
        raise HTTPException(status_code=409, detail="Analysis job still running.")
    if state.status == "failed":
        phase = state.error_phase or "unknown"
        raise HTTPException(
            status_code=500,
            detail=f"Failed during: {phase}",
        )
    return state.result


@app.post("/api/parse-upload")
async def parse_uploaded_file(
    file: UploadFile = File(...),
    ate_log_filename: Optional[str] = Form(None),
):
    if not _is_stil_filename(file.filename or ""):
        raise HTTPException(status_code=400, detail="Only .stil files are supported")

    config = load_config()
    max_gb = config.get("max_file_size_gb", 10.0)

    saved_file_path = os.path.join(STIL_UPLOAD_DIR, os.path.basename(file.filename))

    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        workspace_filename = os.path.relpath(saved_file_path, WORKSPACE_DIR).replace("\\", "/")

        start_time = time.time()
        parser = STILParser()
        report = parser.parse(
            saved_file_path,
            max_size_gb=max_gb,
            waveform_table_mode=_ROBUSTNESS_CFG.stil_validation.waveform_table_mode,
        )
        duration = time.time() - start_time
        report["parsing_duration_seconds"] = round(duration, 3)
        report["workspace_filename"] = workspace_filename

        manual_ate = ate_log_filename.strip() if ate_log_filename else None
        ate_log_path = calculate_and_attach_coverage(report, manual_ate, require_ate=False)

        try:
            write_requirement_outputs(report)
        except Exception as e:
            print(f"Error writing requirement outputs: {str(e)}")

        embedding_summary = run_pa_fr_005_extensions(report, ate_log_path)
        if embedding_summary:
            report["pattern_embeddings"] = embedding_summary
            validation_summary = run_pa_fr_005_validation()
            if validation_summary:
                report["embedding_validation"] = validation_summary

            clustering_summary = run_pa_fr_006_extensions(report)
            if clustering_summary:
                report["pattern_clustering"] = clustering_summary
                redundancy_summary = run_pa_fr_007_extensions(report)
                if redundancy_summary:
                    report["pattern_redundancy"] = redundancy_summary

        return report
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process upload: {str(e)}") from e

@app.post("/api/similarity/pair")
def similarity_pair(req: SimilarityPairRequest):
    try:
        return handle_pair_similarity(req.pattern_a, req.pattern_b, WORKSPACE_DIR, OUTPUT_DIR)
    except SimilarityValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SimilarityAbortError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/api/similarity/top-n")
def similarity_top_n(req: SimilarityTopNRequest):
    try:
        return handle_top_n_similarity(req.reference_pattern, req.top_n, WORKSPACE_DIR, OUTPUT_DIR)
    except SimilarityValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SimilarityAbortError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

@app.post("/api/correlate-pattern-outcomes")
def correlate_pattern_outcomes(req: CorrelatePatternOutcomesRequest):
    try:
        result = handle_correlate_pattern_outcomes(
            workspace_dir=WORKSPACE_DIR,
            output_dir=OUTPUT_DIR,
            ate_log_paths=req.ate_log_paths,
            input_stil=req.input_stil or "",
        )
        try:
            model = write_pattern_quality_report_model(OUTPUT_DIR)
            result["quality_report_model"] = {
                "generated_by": "PA-FR-010.1",
                "filename": REPORT_MODEL_FILENAME,
                "model_hash": model["generation_metadata"]["model_hash"],
                "validation_status": model["generation_metadata"][
                    "validation_status"
                ],
            }
        except Exception as model_exc:
            result["quality_report_model"] = {
                "generated_by": "PA-FR-010.1",
                "status": "WARNING",
                "warning": str(model_exc),
            }
        return result
    except CorrelationAbortedError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/report/preview")
def preview_pattern_quality_report():
    """Return the PA-FR-010.2 preview without generating or modifying files."""
    try:
        return build_report_preview_from_output(OUTPUT_DIR)
    except ReportPreviewError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/analysis-session/report/preview")
def preview_analysis_session_report():
    """Return the PA-FR-010.AS.2 preview without generating or modifying files."""
    try:
        return preview_analysis_session_report_from_output(OUTPUT_DIR)
    except AnalysisSessionReportPreviewError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/analysis-session/report/generate")
def generate_analysis_session_quality_report(req: ReportGenerateRequest):
    """Stream an Analysis Session report without persisting report binaries."""
    try:
        generated = generate_analysis_session_report_from_output(
            OUTPUT_DIR,
            req.format,
        )
    except AnalysisSessionReportGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except AnalysisSessionReportModelError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    # PA-FR-010.AS.5 START
    try:
        append_analysis_session_report_history(
            OUTPUT_DIR,
            format=req.format,
            model_hash=generated.model_hash,
            file_size_bytes=len(generated.content),
            export_type=generated.media_type,
        )
    except AnalysisSessionReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    # PA-FR-010.AS.5 END
    headers = {
        "Content-Disposition": f'attachment; filename="{generated.filename}"',
        "X-Report-Model-Hash": generated.model_hash,
    }
    return StreamingResponse(
        BytesIO(generated.content),
        media_type=generated.media_type,
        headers=headers,
    )


# Phase artifact download (PA-FR-001..003 + Analysis Session 004..006)
PHASE_ARTIFACT_FILES = {
    1: "PA-FR-001_cpm_report.json",
    2: "PA-FR-002_cvm_cycles.csv",
    3: "PA-FR-003_metadata_metrics.json",
    4: SESSION_EXECUTIONS_JSON,
    5: SESSION_EMBEDDINGS_JSON,
    6: SESSION_CLUSTERING_JSON,
}


@app.get("/api/phase-artifacts/{phase}/download")
def download_phase_artifact(phase: int):
    """Download the primary output artifact for phases 1–6 (allowlisted filenames only)."""
    filename = PHASE_ARTIFACT_FILES.get(phase)
    if filename is None:
        raise HTTPException(status_code=404, detail="Unknown phase. Supported phases: 1–6.")
    path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.isfile(path):
        raise HTTPException(
            status_code=404,
            detail=f"Artifact not generated yet: {filename}",
        )
    media_type = (
        "text/csv; charset=utf-8"
        if filename.endswith(".csv")
        else "application/json; charset=utf-8"
    )
    return FileResponse(
        path,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# PA-UI-011 START
@app.post("/api/analysis-session/data-exchange/export")
def export_analysis_session_data_exchange():
    """Stream PA-FR-011 pattern_analysis_master.json without running the pipeline."""
    try:
        master = export_pattern_analysis_master(OUTPUT_DIR, write=True)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    path = os.path.join(OUTPUT_DIR, MASTER_FILENAME)
    return FileResponse(
        path,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="pattern_analysis_master.json"',
            "X-Export-Schema-Version": str(master.get("schema_version") or ""),
        },
    )
# PA-UI-011 END


# PA-FR-010.AS.5 START
@app.get("/api/analysis-session/report/history")
def list_analysis_session_quality_report_history():
    try:
        records = get_analysis_session_report_history(OUTPUT_DIR)
    except AnalysisSessionReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "generated_by": ANALYSIS_SESSION_HISTORY_GENERATOR,
        "history_version": ANALYSIS_SESSION_HISTORY_VERSION,
        "filename": ANALYSIS_SESSION_HISTORY_FILENAME,
        "count": len(records),
        "records": records,
    }


@app.get("/api/analysis-session/report/history/{report_id}")
def read_analysis_session_quality_report_history_entry(report_id: str):
    try:
        record = get_analysis_session_report_history_entry(
            OUTPUT_DIR,
            report_id,
        )
    except AnalysisSessionReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis Session report history entry not found.",
        )
    return record


@app.delete("/api/analysis-session/report/history/{report_id}")
def remove_analysis_session_quality_report_history_entry(report_id: str):
    try:
        deleted = delete_analysis_session_report_history_entry(
            OUTPUT_DIR,
            report_id,
        )
    except AnalysisSessionReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis Session report history entry not found.",
        )
    return {
        "deleted": True,
        "report_id": report_id,
        "record": deleted,
    }
# PA-FR-010.AS.5 END


@app.post("/api/report/generate")
def generate_pattern_quality_report(req: ReportGenerateRequest):
    """Stream a report generated only from the PA-FR-010.1 model."""
    generation_started = time.perf_counter()
    try:
        generated = generate_report_from_output(OUTPUT_DIR, req.format)
    except ReportGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ReportPreviewError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    generation_duration_ms = (time.perf_counter() - generation_started) * 1000
    try:
        report_model = load_report_model(OUTPUT_DIR)
        generation_metadata = report_model.get("generation_metadata") or {}
        history_record = create_history_record(
            report_name="Pattern Quality Report",
            generated_from=REPORT_MODEL_FILENAME,
            generated_timestamp=datetime.now(timezone.utc)
            .isoformat(timespec="microseconds")
            .replace("+00:00", "Z"),
            format=req.format.strip().lower(),
            model_hash=generated.model_hash,
            file_size=len(generated.content),
            status="SUCCESS",
            download_name=generated.filename,
            generation_duration_ms=generation_duration_ms,
            validation_status=str(
                generation_metadata.get("validation_status") or "UNKNOWN"
            ),
        )
        add_history_entry(OUTPUT_DIR, history_record)
    except ReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    headers = {
        "Content-Disposition": f'attachment; filename="{generated.filename}"',
        "X-Report-Model-Hash": generated.model_hash,
    }
    return StreamingResponse(
        BytesIO(generated.content),
        media_type=generated.media_type,
        headers=headers,
    )


@app.get("/api/report/history")
def get_pattern_quality_report_history():
    try:
        records = list_history(OUTPUT_DIR)
    except ReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {
        "generated_by": HISTORY_GENERATOR,
        "history_version": HISTORY_VERSION,
        "filename": HISTORY_FILENAME,
        "count": len(records),
        "records": records,
    }


@app.get("/api/report/history/{report_id}")
def get_pattern_quality_report_history_entry(report_id: str):
    try:
        record = get_history_entry(OUTPUT_DIR, report_id)
    except ReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="Report history entry not found.")
    return record


@app.delete("/api/report/history/{report_id}")
def delete_pattern_quality_report_history_entry(report_id: str):
    try:
        deleted = delete_history_entry(OUTPUT_DIR, report_id)
    except ReportHistoryError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if deleted is None:
        raise HTTPException(status_code=404, detail="Report history entry not found.")
    return {
        "deleted": True,
        "report_id": report_id,
        "record": deleted,
    }


@app.get("/", response_class=HTMLResponse)
def serve_index():
    index_path = os.path.join(WORKSPACE_DIR, "templates", "index.html")
    if not os.path.exists(index_path):
        return HTMLResponse("<h1>index.html not found! Please create it.</h1>", status_code=404)
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(
        content=html,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
        },
    )
