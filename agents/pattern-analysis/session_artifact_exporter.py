"""
Session artifact exporter — writes PA-Analysis-Session_* JSON files only.

Never writes or modifies completed FR output artifacts.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Sequence, Tuple

from analysis_session_report_model_builder import (
    REPORT_MODEL_FILENAME,
    session_executions_artifact_payload,
    write_analysis_session_report_model,
)
from analysis_session_similarity_exporter import (
    build_analysis_session_similarity,
)
from analysis_session_cache import (
    file_sha256 as cache_file_sha256,
    try_warm_cache,
    write_cache_record,
)
from analysis_session import (
    SESSION_ARTIFACT_FILENAMES,
    SESSION_CLUSTERING_JSON,
    SESSION_CORRELATION_JSON,
    SESSION_EMBEDDINGS_JSON,
    SESSION_EXECUTIONS_JSON,
    SESSION_MANIFEST_JSON,
    SESSION_REDUNDANCY_JSON,
    SESSION_SCAN_VECTORS_JSON,
    SESSION_SIMILARITY_JSON,
    SESSION_SUMMARY_JSON,
    AnalysisSession,
    SessionPathError,
    build_session_manifest,
    requires_session_path,
    resolve_session_log_paths,
)
from session_cache_exporter import build_session_scan_vectors
from session_cluster_exporter import build_session_clustering
from session_config import load_session_config, resolve_e0_parallel_workers
from session_correlation_exporter import build_session_correlation
from session_embedding_exporter import build_session_embeddings
from session_execution_normalizer import build_session_executions
from session_log_cache import build_session_log_cache
from session_perf_trace import (
    SessionPerfTrace,
    optional_phase,
    write_session_perf_trace,
)
from session_redundancy_exporter import build_session_redundancy
from session_summary import derive_session_summary, load_summary_from_config_path


logger = logging.getLogger(__name__)

# PA-PERF-006 — internal scheduler feature (not a public engineering knob).
# Overlaps Correlation with Scan Vectors → … → Redundancy. Set False for serial debug.
ENABLE_CORRELATION_OVERLAP = True


def _write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _write_similarity_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            payload,
            handle,
            sort_keys=True,
            indent=2,
            ensure_ascii=False,
        )


def _file_sha256(path: str) -> str:
    """Hash on-disk bytes after write (matches report-model provenance)."""
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timed_artifact_write(
    *,
    path: str,
    payload: Any,
    artifact_name: str,
    perf_trace: Optional[SessionPerfTrace],
    writer,
) -> str:
    """Write one artifact; return SHA-256 of the on-disk file bytes."""
    started = time.perf_counter()
    writer(path, payload)
    serialize_ms = (time.perf_counter() - started) * 1000.0
    artifact_hash = _file_sha256(path)
    if perf_trace is not None:
        try:
            nbytes = os.path.getsize(path) if os.path.exists(path) else 0
            perf_trace.record_write(
                artifact=artifact_name,
                serialize_ms=serialize_ms,
                nbytes=nbytes,
            )
        except Exception:
            logger.exception(
                "Analysis Session perf write telemetry failed for %s; continuing.",
                artifact_name,
            )
    return artifact_hash


def _resolve_config_path(workspace_dir: str, config_path: Optional[str]) -> str:
    if config_path:
        return config_path
    candidate = os.path.join(workspace_dir, "config", "analysis_session.yaml")
    if os.path.exists(candidate):
        return candidate
    # Fall back to repo config when tests use an empty temp workspace.
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "config",
        "analysis_session.yaml",
    )


def _resolve_metadata_path(output_dir: str, metadata_path: Optional[str]) -> Optional[str]:
    if metadata_path:
        return metadata_path
    candidate = os.path.join(output_dir, "PA-FR-003_metadata_metrics.json")
    return candidate if os.path.exists(candidate) else None


def build_analysis_session(
    *,
    workspace_dir: str,
    stil_file: str,
    requested_log_paths: Sequence[str],
    generated_timestamp: Optional[str] = None,
    config_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    perf_trace: Optional[SessionPerfTrace] = None,
) -> AnalysisSession:
    """
    Build an in-memory Analysis Session for multi-log workflows.

    Raises SessionPathError when fewer than two logs are supplied.
    """
    if not requires_session_path(list(requested_log_paths)):
        raise SessionPathError(
            "Analysis Session requires two or more ATE logs. "
            "Use the legacy single-log pipeline for one log."
        )

    absolute_paths, relative_paths = resolve_session_log_paths(workspace_dir, requested_log_paths)
    manifest = build_session_manifest(
        stil_file=stil_file,
        input_ate_logs=relative_paths,
        generated_timestamp=generated_timestamp,
    )
    if perf_trace is not None:
        perf_trace.session_hash = manifest.get("session_hash")

    resolved_config_path = _resolve_config_path(workspace_dir, config_path)
    config = load_summary_from_config_path(resolved_config_path)
    e0_workers = resolve_e0_parallel_workers(
        config.e0_parallel_workers,
        log_count=len(absolute_paths),
    )

    # E0: parse each ATE log once; reuse across executions / vectors / embeddings.
    with optional_phase(perf_trace, "e0_log_cache"):
        log_entries = build_session_log_cache(
            absolute_paths,
            relative_paths,
            max_workers=e0_workers,
        )

    with optional_phase(perf_trace, "executions"):
        executions = build_session_executions(
            workspace_dir,
            absolute_paths,
            relative_paths,
            log_entries=log_entries,
        )

    with optional_phase(perf_trace, "summary"):
        summary = derive_session_summary(executions, config=config)

    session_hash = manifest.get("session_hash")
    correlation = None
    correlation_future = None
    overlap_executor = None

    if ENABLE_CORRELATION_OVERLAP:
        if perf_trace is not None:
            perf_trace.add_note("correlation_overlap=enabled")

        def _run_correlation():
            with optional_phase(perf_trace, "correlation"):
                return build_session_correlation(
                    executions,
                    session_hash=session_hash,
                )

        overlap_executor = ThreadPoolExecutor(max_workers=1)
        correlation_future = overlap_executor.submit(_run_correlation)
    else:
        if perf_trace is not None:
            perf_trace.add_note("correlation_overlap=disabled")

    try:
        with optional_phase(perf_trace, "scan_vectors"):
            scan_vectors = build_session_scan_vectors(
                stil_file=stil_file,
                absolute_log_paths=absolute_paths,
                relative_log_paths=relative_paths,
                log_entries=log_entries,
            )

        resolved_metadata = metadata_path
        if resolved_metadata is None and output_dir:
            resolved_metadata = _resolve_metadata_path(output_dir, None)

        with optional_phase(perf_trace, "embeddings"):
            embeddings = build_session_embeddings(
                stil_file=stil_file,
                scan_vectors=scan_vectors,
                absolute_log_paths=absolute_paths,
                relative_log_paths=relative_paths,
                config=config,
                metadata_path=resolved_metadata,
                log_entries=log_entries,
            )

        similarity = None
        with optional_phase(perf_trace, "similarity"):
            try:
                similarity = build_analysis_session_similarity(
                    embeddings_payload=embeddings,
                    manifest=manifest,
                    workspace_dir=workspace_dir,
                )
            except Exception:
                logger.exception(
                    "Analysis Session similarity artifact generation failed; "
                    "the deterministic session pipeline will continue."
                )

        clustering = build_session_clustering(
            embeddings_payload=embeddings,
            workspace_dir=workspace_dir,
            summary=summary,
            input_ate_logs=relative_paths,
            session_hash=session_hash,
            perf_trace=perf_trace,
        )

        redundancy = build_session_redundancy(
            clustering_payload=clustering,
            embeddings_payload=embeddings,
            workspace_dir=workspace_dir,
            session_hash=session_hash,
            perf_trace=perf_trace,
        )

        if correlation_future is not None:
            with optional_phase(perf_trace, "wait_for_correlation"):
                correlation = correlation_future.result()
        else:
            with optional_phase(perf_trace, "correlation"):
                correlation = build_session_correlation(
                    executions,
                    session_hash=session_hash,
                )
    finally:
        if overlap_executor is not None:
            overlap_executor.shutdown(wait=True)

    return AnalysisSession(
        manifest=manifest,
        executions=executions,
        summary=summary,
        scan_vectors=scan_vectors,
        embeddings=embeddings,
        similarity=similarity,
        clustering=clustering,
        redundancy=redundancy,
        correlation=correlation,
    )


def write_session_artifacts(
    output_dir: str,
    session: AnalysisSession,
    *,
    perf_trace: Optional[SessionPerfTrace] = None,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Persist session artifacts to disk.

    Returns (paths, artifact_hashes) where:
      - paths: logical artifact name → absolute file path
      - artifact_hashes: filename → SHA-256 of on-disk bytes
    Only PA-Analysis-Session_* files are written.
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = {
        "manifest": os.path.join(output_dir, SESSION_MANIFEST_JSON),
        "executions": os.path.join(output_dir, SESSION_EXECUTIONS_JSON),
        "summary": os.path.join(output_dir, SESSION_SUMMARY_JSON),
        "scan_vectors": os.path.join(output_dir, SESSION_SCAN_VECTORS_JSON),
        "embeddings": os.path.join(output_dir, SESSION_EMBEDDINGS_JSON),
        "similarity": os.path.join(output_dir, SESSION_SIMILARITY_JSON),
        "clustering": os.path.join(output_dir, SESSION_CLUSTERING_JSON),
        "redundancy": os.path.join(output_dir, SESSION_REDUNDANCY_JSON),
        "correlation": os.path.join(output_dir, SESSION_CORRELATION_JSON),
    }
    artifact_hashes: Dict[str, str] = {}

    artifact_hashes[SESSION_MANIFEST_JSON] = _timed_artifact_write(
        path=paths["manifest"],
        payload=session.manifest,
        artifact_name=SESSION_MANIFEST_JSON,
        perf_trace=perf_trace,
        writer=_write_json,
    )
    artifact_hashes[SESSION_EXECUTIONS_JSON] = _timed_artifact_write(
        path=paths["executions"],
        payload=session_executions_artifact_payload(session.executions),
        artifact_name=SESSION_EXECUTIONS_JSON,
        perf_trace=perf_trace,
        writer=_write_json,
    )
    artifact_hashes[SESSION_SUMMARY_JSON] = _timed_artifact_write(
        path=paths["summary"],
        payload=session.summary,
        artifact_name=SESSION_SUMMARY_JSON,
        perf_trace=perf_trace,
        writer=_write_json,
    )

    if session.scan_vectors is not None:
        artifact_hashes[SESSION_SCAN_VECTORS_JSON] = _timed_artifact_write(
            path=paths["scan_vectors"],
            payload=session.scan_vectors,
            artifact_name=SESSION_SCAN_VECTORS_JSON,
            perf_trace=perf_trace,
            writer=_write_json,
        )
    if session.embeddings is not None:
        artifact_hashes[SESSION_EMBEDDINGS_JSON] = _timed_artifact_write(
            path=paths["embeddings"],
            payload=session.embeddings,
            artifact_name=SESSION_EMBEDDINGS_JSON,
            perf_trace=perf_trace,
            writer=_write_json,
        )
    if session.similarity is not None:
        artifact_hashes[SESSION_SIMILARITY_JSON] = _timed_artifact_write(
            path=paths["similarity"],
            payload=session.similarity,
            artifact_name=SESSION_SIMILARITY_JSON,
            perf_trace=perf_trace,
            writer=_write_similarity_json,
        )
    if session.clustering is not None:
        artifact_hashes[SESSION_CLUSTERING_JSON] = _timed_artifact_write(
            path=paths["clustering"],
            payload=session.clustering,
            artifact_name=SESSION_CLUSTERING_JSON,
            perf_trace=perf_trace,
            writer=_write_json,
        )
    if session.redundancy is not None:
        artifact_hashes[SESSION_REDUNDANCY_JSON] = _timed_artifact_write(
            path=paths["redundancy"],
            payload=session.redundancy,
            artifact_name=SESSION_REDUNDANCY_JSON,
            perf_trace=perf_trace,
            writer=_write_json,
        )
    if session.correlation is not None:
        artifact_hashes[SESSION_CORRELATION_JSON] = _timed_artifact_write(
            path=paths["correlation"],
            payload=session.correlation,
            artifact_name=SESSION_CORRELATION_JSON,
            perf_trace=perf_trace,
            writer=_write_json,
        )

    return paths, artifact_hashes


def run_analysis_session_pipeline(
    *,
    workspace_dir: str,
    output_dir: str,
    stil_file: str,
    requested_log_paths: Sequence[str],
    generated_timestamp: Optional[str] = None,
    config_path: Optional[str] = None,
    metadata_path: Optional[str] = None,
) -> AnalysisSession:
    """Build and write a multi-log Analysis Session. Does not touch FR artifacts."""
    perf_trace = SessionPerfTrace()
    session: Optional[AnalysisSession] = None
    try:
        resolved_config_path = _resolve_config_path(workspace_dir, config_path)
        session_config = load_session_config(resolved_config_path)

        with optional_phase(perf_trace, "warm_cache_lookup"):
            warm_result, cache_identity = try_warm_cache(
                workspace_dir=workspace_dir,
                output_dir=output_dir,
                stil_file=stil_file,
                requested_log_paths=requested_log_paths,
                config_path=resolved_config_path,
                enabled=bool(session_config.session_warm_cache),
            )

        if warm_result.hit and warm_result.session is not None:
            session = warm_result.session
            perf_trace.session_hash = session.manifest.get("session_hash")
            perf_trace.add_note(
                f"warm_cache_hit reason={warm_result.reason} "
                f"validation_ms={warm_result.validation_ms}"
            )
            report_path = os.path.join(output_dir, REPORT_MODEL_FILENAME)
            if not os.path.exists(report_path):
                artifact_hashes = {
                    name: cache_file_sha256(os.path.join(output_dir, name))
                    for name in SESSION_ARTIFACT_FILENAMES
                    if os.path.exists(os.path.join(output_dir, name))
                }
                with optional_phase(perf_trace, "report_model"):
                    try:
                        write_analysis_session_report_model(
                            output_dir,
                            session=session,
                            artifact_hashes=artifact_hashes,
                        )
                    except Exception:
                        logger.exception(
                            "Analysis Session report model generation failed; "
                            "core Analysis Session artifacts remain available."
                        )
            return session

        perf_trace.add_note(
            f"warm_cache_miss reason={warm_result.reason} "
            f"validation_ms={warm_result.validation_ms}"
        )

        session = build_analysis_session(
            workspace_dir=workspace_dir,
            stil_file=stil_file,
            requested_log_paths=requested_log_paths,
            generated_timestamp=generated_timestamp,
            config_path=config_path,
            metadata_path=metadata_path,
            output_dir=output_dir,
            perf_trace=perf_trace,
        )
        _paths, artifact_hashes = write_session_artifacts(
            output_dir, session, perf_trace=perf_trace
        )
        try:
            write_cache_record(
                output_dir,
                identity=cache_identity,
                artifact_hashes=artifact_hashes,
                session_hash=str(session.manifest.get("session_hash") or ""),
            )
        except Exception:
            logger.exception(
                "Analysis Session warm cache record write failed; "
                "core Analysis Session artifacts remain available."
            )
        with optional_phase(perf_trace, "ml_001_inference"):
            try:
                # Lazy import keeps offline training package out of the session module graph.
                from ml.inference_001 import run_pa_ml_001_inference
                from ml.inference_001_lot import run_pa_ml_001_lot_inference

                run_pa_ml_001_inference(output_dir, workspace_dir)
                run_pa_ml_001_lot_inference(output_dir, workspace_dir)
            except Exception:
                logger.exception(
                    "PA-ML-001 inference failed; "
                    "core Analysis Session artifacts remain available."
                )
        with optional_phase(perf_trace, "ml_002_inference"):
            try:
                from ml.inference_002 import run_pa_ml_002_inference
                from ml.inference_002_lot import run_pa_ml_002_lot_inference

                run_pa_ml_002_inference(output_dir, workspace_dir)
                run_pa_ml_002_lot_inference(output_dir, workspace_dir)
            except Exception:
                logger.exception(
                    "PA-ML-002 inference failed; "
                    "core Analysis Session artifacts remain available."
                )
        with optional_phase(perf_trace, "ml_003_inference"):
            try:
                from ml.inference_003 import run_pa_ml_003_inference
                from ml.inference_003_lot import run_pa_ml_003_lot_inference

                run_pa_ml_003_inference(output_dir, workspace_dir)
                run_pa_ml_003_lot_inference(output_dir, workspace_dir)
            except Exception:
                logger.exception(
                    "PA-ML-003 inference failed; "
                    "core Analysis Session artifacts remain available."
                )
        with optional_phase(perf_trace, "ml_004_inference"):
            try:
                from ml.inference_004 import run_pa_ml_004_inference
                from ml.inference_004_lot import run_pa_ml_004_lot_inference

                run_pa_ml_004_inference(output_dir, workspace_dir)
                run_pa_ml_004_lot_inference(output_dir, workspace_dir)
            except Exception:
                logger.exception(
                    "PA-ML-004 inference failed; "
                    "core Analysis Session artifacts remain available."
                )
        with optional_phase(perf_trace, "report_model"):
            try:
                write_analysis_session_report_model(
                    output_dir,
                    session=session,
                    artifact_hashes=artifact_hashes,
                )
            except Exception:
                logger.exception(
                    "Analysis Session report model generation failed; "
                    "core Analysis Session artifacts remain available."
                )
        return session
    finally:
        try:
            session_hash = (
                session.manifest.get("session_hash")
                if session is not None
                else perf_trace.session_hash
            )
            write_session_perf_trace(
                output_dir,
                perf_trace,
                session_hash=session_hash,
            )
        except Exception:
            logger.exception(
                "Analysis Session perf trace finalization failed; "
                "core Analysis Session artifacts remain available."
            )
