"""
FastAPI REST interface for WaferVision-AI.

Responsibility: request validation and response delivery ONLY.
Contains zero engineering / ML business logic.

Every analysis endpoint validates the upload, then calls
``run_wafer_analysis()`` / ``run_batch_analysis()`` and returns that JSON
unchanged.

Operational endpoints (``/health``, ``/version``, ``/metrics``) are
infrastructure-only and do not alter inference outputs.
"""

from __future__ import annotations

import logging
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import (
    API_ALLOWED_EXTENSIONS,
    API_ALLOWED_ORIGINS,
    API_HOST,
    API_KEEPALIVE_SECONDS,
    API_MAX_BATCH_FILES,
    API_MAX_UPLOAD_BYTES,
    API_PORT,
    API_REQUEST_TIMEOUT_SECONDS,
    API_TITLE,
    API_VERSION,
    API_WORKERS,
    INPUT_ROOT,
    MODEL_PATH,
    OUTPUT_ROOT,
    TEMP_DIR,
)
from .errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from .health import get_health_status, get_metrics, get_version_info
from .logging_config import configure_logging, get_batch_logger
from .model import get_device
from .predict import load_prediction_model
from .response_models import PredictionResponse
from .schemas import GridMode, HealthResponse, MetricsResponse, VersionResponse
from .wafer_pipeline import PipelineError, run_batch_analysis, run_wafer_analysis

logger = logging.getLogger(__name__)
batch_logger = get_batch_logger()

_FORBIDDEN_SUFFIXES: frozenset[str] = frozenset(
    {
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".msi",
        ".scr",
        ".ps1",
        ".sh",
        ".dll",
        ".so",
        ".jar",
        ".js",
        ".vbs",
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".tgz",
        ".bz2",
        ".xz",
    }
)


def _sanitize_filename(filename: str | None) -> str:
    """
    Sanitize an upload filename for safe temporary storage.

    Prevents path traversal by stripping directories and normalizing characters.

    Args:
        filename: Raw upload filename.

    Returns:
        Safe basename suitable for TEMP_DIR.
    """
    raw = Path(filename or "upload.bin").name
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("._")
    return cleaned or "upload.bin"


def _validate_upload_file(upload: UploadFile, payload: bytes) -> str:
    """
    Validate uploaded bytes and return a sanitized filename.

    Args:
        upload: FastAPI upload object.
        payload: Raw file bytes.

    Returns:
        Sanitized filename.

    Raises:
        HTTPException: On empty, oversized, or unsupported files.
    """
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image is empty.",
        )
    if len(payload) > API_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Upload exceeds maximum size of "
                f"{API_MAX_UPLOAD_BYTES} bytes."
            ),
        )

    filename = _sanitize_filename(upload.filename)
    # Reject path traversal remnants after sanitization
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    suffix = Path(filename).suffix.lower()
    if suffix in _FORBIDDEN_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Executable / archive / disallowed file type rejected: {suffix}",
        )
    if suffix not in API_ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=(
                f"Unsupported media type '{suffix}'. "
                f"Allowed: {sorted(API_ALLOWED_EXTENSIONS)}"
            ),
        )

    content_type = (upload.content_type or "").lower()
    if content_type and not (
        content_type.startswith("image/")
        or content_type in {"application/octet-stream"}
    ):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported Content-Type: {content_type}",
        )
    return filename


def _parse_grid_mode(grid_mode: str) -> str:
    """Normalize and validate grid_mode form field."""
    normalized = (grid_mode or "automatic").strip().lower()
    if normalized not in {GridMode.automatic.value, GridMode.manual.value}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="grid_mode must be 'automatic' or 'manual'.",
        )
    return normalized


IMAGE_SET_KEYS: tuple[str, ...] = (
    "original",
    "overlay",
    "density",
    "gradcam",
    "heatmap",
)


def _parse_image_set(include_images: str) -> tuple[str, ...]:
    """
    Resolve the ``include_images`` form field into the PNG keys to return.

    Accepts ``all``/``true`` (legacy clients), ``none``/``false`` (canvas
    clients rendering ``visualization`` JSON), or a comma-separated subset such
    as ``original`` for clients that only need the wafer photo as a base layer.
    """
    token = (include_images or "all").strip().lower()
    if token in {"all", "true", "1", "yes"}:
        return IMAGE_SET_KEYS
    if token in {"none", "false", "0", "no"}:
        return ()
    keys = tuple(
        key for key in (part.strip() for part in token.split(",")) if key in IMAGE_SET_KEYS
    )
    if not keys:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "include_images must be all, none, or a comma-separated subset of "
                f"{', '.join(IMAGE_SET_KEYS)}."
            ),
        )
    return keys


def _apply_image_set(result: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    """Trim the encoded PNG bundle down to the keys the client asked for."""
    images = result.get("images")
    if not isinstance(images, dict):
        return result
    if not keys:
        result.pop("images", None)
        return result
    result["images"] = {key: value for key, value in images.items() if key in keys}
    return result


def _resolve_grid_size(grid_mode: str, grid_size: Optional[int]) -> Optional[int]:
    """Validate manual grid_size requirements."""
    if grid_mode == GridMode.manual.value:
        if grid_size is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="grid_size is required when grid_mode='manual' (e.g. 52).",
            )
        if grid_size < 2 or grid_size > 256:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="grid_size must be between 2 and 256.",
            )
        return int(grid_size)
    return None


async def _save_upload_to_temp(upload: UploadFile) -> Path:
    """Read, validate, and persist an upload under TEMP_DIR (legacy helper)."""
    payload = await upload.read()
    filename = _validate_upload_file(upload, payload)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time() * 1000)
    destination = TEMP_DIR / f"api_{stamp}_{filename}"
    destination = TEMP_DIR / destination.name
    destination.write_bytes(payload)
    return destination


def _new_session_id() -> str:
    return f"wafer_{int(time.time() * 1000)}"


def _session_input_dir(session_id: str) -> Path:
    path = INPUT_ROOT / session_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def _session_output_dir(session_id: str) -> Path:
    path = OUTPUT_ROOT / session_id / "wafer"
    path.mkdir(parents=True, exist_ok=True)
    (path / "images").mkdir(parents=True, exist_ok=True)
    (path / "logs").mkdir(parents=True, exist_ok=True)
    return path


async def _save_upload_to_session(upload: UploadFile, session_id: str) -> Path:
    """Persist upload under ``C:\\personal\\input all file\\<session_id>\\``."""
    payload = await upload.read()
    filename = _validate_upload_file(upload, payload)
    destination = _session_input_dir(session_id) / filename
    if destination.exists():
        stem, suffix = destination.stem, destination.suffix
        n = 1
        while True:
            candidate = destination.with_name(f"{stem}_{n}{suffix}")
            if not candidate.exists():
                destination = candidate
                break
            n += 1
    destination.write_bytes(payload)
    return destination


def _persist_session_result(session_id: str, result: dict[str, Any], image_path: Path) -> None:
    """Write analysis JSON (+ optional image refs) under agent output root."""
    import base64
    import json

    out_dir = _session_output_dir(session_id)
    stem = image_path.stem
    payload = {k: v for k, v in result.items() if k != "images"}
    payload["input_path"] = str(image_path)
    payload["session_id"] = session_id
    meta_path = out_dir / f"{stem}.json"
    meta_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    images = result.get("images") or {}
    for kind, b64 in images.items():
        if not isinstance(b64, str) or not b64:
            continue
        try:
            raw = b64.split(",", 1)[-1] if b64.startswith("data:") else b64
            data = base64.b64decode(raw)
            (out_dir / "images" / f"{stem}_{kind}.png").write_bytes(data)
        except Exception:  # noqa: BLE001
            logger.warning("Failed to persist %s image for %s", kind, stem)

    result["input_path"] = str(image_path)
    result["session_id"] = session_id
    result["output_path"] = str(meta_path)


def _cleanup_temp(path: Path) -> None:
    """Best-effort temp file cleanup (session inputs are kept permanently)."""
    try:
        # Never delete durable personal input roots
        if INPUT_ROOT in path.resolve().parents or path.resolve().parent == INPUT_ROOT.resolve():
            return
        path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Failed to remove temp upload: %s", path)


def _log_analysis_summary(
    *,
    image_name: str,
    request_ms: float,
    result: dict[str, Any],
) -> None:
    """Log request metadata without base64 image payloads."""
    classification = result.get("classification") or {}
    yield_summary = result.get("yield_summary") or {}
    timing = result.get("timing_ms") or {}
    logger.info(
        "image=%s request_ms=%.1f inference_ms=%s prediction=%s "
        "confidence=%s yield=%.2f%% total_dies=%s",
        image_name,
        request_ms,
        timing.get("prediction"),
        classification.get("defect_type"),
        classification.get("confidence"),
        float(yield_summary.get("yield_percent", 0.0)),
        yield_summary.get("total_dies"),
    )


async def _run_single_upload_analysis(
    image: UploadFile,
    grid_mode: str,
    grid_size: Optional[int],
    include_images: str = "all",
) -> dict[str, Any]:
    """Validate one upload and return unmodified pipeline JSON."""
    started = time.perf_counter()
    image_keys = _parse_image_set(include_images)
    mode = _parse_grid_mode(grid_mode)
    size = _resolve_grid_size(mode, grid_size)
    session_id = _new_session_id()
    input_path: Path | None = None
    try:
        input_path = await _save_upload_to_session(image, session_id)
        result = run_wafer_analysis(
            input_path,
            grid_mode=mode,
            grid_size=size,
            wafer_id=input_path.name,
            save_log=True,
            include_images=bool(image_keys),
        )
        _apply_image_set(result, image_keys)
        _persist_session_result(session_id, result, input_path)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        _log_analysis_summary(
            image_name=input_path.name,
            request_ms=elapsed_ms,
            result=result,
        )
        return result
    except HTTPException:
        raise
    except PipelineError as exc:
        logger.exception("Pipeline failure during upload analysis")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled upload analysis error")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during wafer analysis.",
        ) from exc


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI instance with analysis + system routes.
    """

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        device = get_device()
        logger.info("=" * 50)
        logger.info("DEVICE: %s", device)
        logger.info("MODEL PATH: %s", MODEL_PATH)
        logger.info("=" * 50)
        try:
            load_prediction_model(MODEL_PATH, device=device)
            logger.info("CNN checkpoint loaded")
        except Exception as exc:  # noqa: BLE001
            logger.error("CNN checkpoint required for Grad-CAM images: %s", exc)
            raise
        logger.info("FastAPI running http://%s:%s", API_HOST, API_PORT)
        logger.info("WaferVision-AI API startup complete on %s", device)
        yield
        logger.info("WaferVision-AI API shutdown")

    application = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=(
            "Production REST API for WaferVision-AI.\n\n"
            "Thin interface over ``run_wafer_analysis()`` — no ML logic in routes.\n\n"
            "**Analysis:** `POST /predict`, `POST /analyze`, `POST /predict/batch`\n\n"
            "**Operations:** `GET /`, `GET /health`, `GET /version`, `GET /metrics`\n\n"
            "Analysis responses are the exact pipeline JSON "
            "(classification, yield, dies, images, spatial_analysis)."
        ),
        lifespan=lifespan,
    )

    application.add_exception_handler(StarletteHTTPException, http_exception_handler)
    application.add_exception_handler(RequestValidationError, validation_exception_handler)
    application.add_exception_handler(Exception, unhandled_exception_handler)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=API_ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.middleware("http")
    async def request_logging_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        logger.info(
            "request method=%s path=%s status=%s duration_ms=%.1f",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    # ------------------------------------------------------------------
    # System / operations
    # ------------------------------------------------------------------

    @application.get(
        "/",
        response_model=HealthResponse,
        summary="Root health check",
        description="Legacy root probe confirming the API process is running.",
        tags=["system"],
        responses={200: {"description": "API is running"}},
    )
    async def root() -> HealthResponse:
        return HealthResponse(message="WaferVision-AI API Running")

    @application.get(
        "/health",
        summary="Detailed health check",
        description=(
            "Returns readiness information including whether the singleton "
            "prediction model is loaded. Does not run inference."
        ),
        tags=["system"],
        responses={
            200: {"description": "Health payload"},
        },
    )
    async def health() -> JSONResponse:
        return JSONResponse(content=get_health_status())

    @application.get(
        "/version",
        response_model=VersionResponse,
        summary="Semantic version",
        description="Returns application and model version metadata.",
        tags=["system"],
    )
    async def version() -> VersionResponse:
        info = get_version_info()
        return VersionResponse(**info)

    @application.get(
        "/metrics",
        response_model=None,
        summary="Operational metrics",
        description=(
            "Lightweight process metrics (memory / CPU / disk when psutil is "
            "installed). Never returns wafer images or pipeline JSON."
        ),
        tags=["system"],
        responses={200: {"model": MetricsResponse}},
    )
    async def metrics() -> JSONResponse:
        return JSONResponse(content=get_metrics())

    # ------------------------------------------------------------------
    # Analysis — response bodies are unmodified pipeline JSON
    # ------------------------------------------------------------------

    @application.post(
        "/predict",
        response_model=None,
        summary="Analyze a single wafer image",
        description=(
            "Accepts a wafer inspection image and optional grid settings, "
            "then returns the exact JSON produced by ``run_wafer_analysis()``.\n\n"
            "**Supported formats:** jpg, jpeg, png, bmp\n\n"
            "**Automatic grid:** omit ``grid_size``.\n\n"
            "**Manual grid:** set ``grid_mode=manual`` and ``grid_size`` "
            "(e.g. 52 → 52×52). Pitch/offset/radius/center are internal.\n\n"
            "**Example form fields:** `image=@wafer.jpg`, "
            "`grid_mode=automatic`"
        ),
        tags=["analysis"],
        responses={
            200: {
                "description": "Pipeline analysis JSON (unchanged).",
                "model": PredictionResponse,
            },
            400: {"description": "Invalid request / empty / oversized upload"},
            415: {"description": "Unsupported media type"},
            422: {"description": "Validation error"},
            500: {"description": "Internal server error"},
        },
    )
    async def predict(
        image: UploadFile = File(..., description="Wafer image file"),
        grid_mode: str = Form(
            "automatic",
            description="automatic | manual",
            examples=["automatic"],
        ),
        grid_size: Optional[int] = Form(
            None,
            description="Required for manual mode (rows=columns=grid_size)",
            examples=[52],
        ),
        include_images: str = Form(
            "all",
            description=(
                "Base64 PNG panels to return: `all` (legacy clients), `none`, or "
                "a subset such as `original` for canvas clients that render the "
                "`visualization` JSON over the wafer photo."
            ),
            examples=["all", "none", "original"],
        ),
    ) -> JSONResponse:
        result = await _run_single_upload_analysis(
            image, grid_mode, grid_size, include_images
        )
        return JSONResponse(content=result)

    @application.post(
        "/analyze",
        response_model=None,
        summary="Analyze a single wafer image (alias of /predict)",
        description="Identical behaviour and response to ``POST /predict``.",
        tags=["analysis"],
        responses={
            200: {
                "description": "Pipeline analysis JSON (unchanged).",
                "model": PredictionResponse,
            }
        },
    )
    async def analyze(
        image: UploadFile = File(..., description="Wafer image file"),
        grid_mode: str = Form("automatic"),
        grid_size: Optional[int] = Form(None),
        include_images: str = Form("all"),
    ) -> JSONResponse:
        result = await _run_single_upload_analysis(
            image, grid_mode, grid_size, include_images
        )
        return JSONResponse(content=result)

    @application.post(
        "/predict/batch",
        response_model=None,
        summary="Analyze multiple wafer images",
        description=(
            "Accepts multiple wafer images and returns a JSON list of "
            "``run_wafer_analysis()`` results. Reuses the singleton model.\n\n"
            f"Maximum batch size: {API_MAX_BATCH_FILES} files "
            f"(``WAFERVISION_MAX_BATCH_FILES``)."
        ),
        tags=["analysis"],
        responses={
            200: {"description": "List of pipeline analysis JSON objects"},
            400: {"description": "Invalid request"},
            415: {"description": "Unsupported media type"},
            422: {"description": "Validation error"},
            500: {"description": "Internal server error"},
        },
    )
    async def predict_batch(
        images: list[UploadFile] = File(
            ...,
            description="One or more wafer image files",
        ),
        grid_mode: str = Form("automatic"),
        grid_size: Optional[int] = Form(None),
        include_images: str = Form("all"),
    ) -> JSONResponse:
        if not images:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one image is required.",
            )
        if len(images) > API_MAX_BATCH_FILES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Batch exceeds maximum of {API_MAX_BATCH_FILES} images."
                ),
            )

        image_keys = _parse_image_set(include_images)
        mode = _parse_grid_mode(grid_mode)
        size = _resolve_grid_size(mode, grid_size)
        session_id = _new_session_id()
        input_paths: list[Path] = []
        started = time.perf_counter()
        try:
            for upload in images:
                input_paths.append(await _save_upload_to_session(upload, session_id))

            results = run_batch_analysis(
                input_paths,
                grid_mode=mode,
                grid_size=size,
                save_log=True,
                include_images=bool(image_keys),
            )
            for result, input_path in zip(results, input_paths):
                if isinstance(result, dict):
                    _apply_image_set(result, image_keys)
                    _persist_session_result(session_id, result, input_path)

            import json

            batch_path = _session_output_dir(session_id) / "batch_result.json"
            batch_payload = [
                {k: v for k, v in r.items() if k != "images"} if isinstance(r, dict) else r
                for r in results
            ]
            batch_path.write_text(
                json.dumps(batch_payload, indent=2, default=str), encoding="utf-8"
            )

            elapsed_ms = (time.perf_counter() - started) * 1000.0
            batch_logger.info(
                "batch_count=%d request_ms=%.1f session=%s",
                len(results),
                elapsed_ms,
                session_id,
            )
            return JSONResponse(content=results)
        except HTTPException:
            raise
        except PipelineError as exc:
            logger.exception("Pipeline failure for /predict/batch")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("Unhandled /predict/batch error")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error during batch analysis.",
            ) from exc

    return application


def run_server(
    *,
    host: str = API_HOST,
    port: int = API_PORT,
    reload: bool = False,
    workers: int = API_WORKERS,
) -> None:
    """
    Run the API with Uvicorn.

    Args:
        host: Bind host.
        port: Bind port.
        reload: Enable auto-reload (development).
        workers: Worker processes (production). Ignored when reload=True.
    """
    configure_logging()
    uvicorn_kwargs: dict[str, Any] = {
        "host": host,
        "port": port,
        "reload": reload,
        "timeout_keep_alive": API_KEEPALIVE_SECONDS,
        "timeout_graceful_shutdown": int(min(API_REQUEST_TIMEOUT_SECONDS, 30)),
    }
    if not reload and workers > 1:
        uvicorn_kwargs["workers"] = workers
    uvicorn.run("src.api:app", **uvicorn_kwargs)


app = create_app()


def main() -> None:
    """CLI entry: ``python -m src.api``."""
    run_server()


__all__ = [
    "create_app",
    "run_server",
    "app",
    "main",
]


if __name__ == "__main__":
    main()
