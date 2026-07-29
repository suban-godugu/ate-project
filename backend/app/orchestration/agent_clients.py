"""HTTP clients for Pattern / Failure / Scan Diagnosis run APIs."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.core.config import get_settings

log = logging.getLogger("verilumen.agent_clients")
settings = get_settings()


class AgentClientError(Exception):
    def __init__(self, agent: str, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.agent = agent
        self.status_code = status_code


def _headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "X-Verilumen-Service-Key": settings.verilumen_service_key,
    }


async def _post_with_retry(agent: str, url: str, payload: dict[str, Any]) -> dict[str, Any]:
    retries = max(1, settings.agent_http_retries)
    timeout = settings.agent_http_timeout_sec
    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, retries + 1):
            try:
                resp = await client.post(url, json=payload, headers=_headers())
                if resp.status_code >= 500:
                    raise AgentClientError(
                        agent, f"HTTP {resp.status_code}: {resp.text[:500]}", status_code=resp.status_code
                    )
                if resp.status_code >= 400:
                    raise AgentClientError(
                        agent, f"HTTP {resp.status_code}: {resp.text[:500]}", status_code=resp.status_code
                    )
                data = resp.json()
                if not isinstance(data, dict):
                    return {"raw": data}
                return data
            except (httpx.HTTPError, AgentClientError) as exc:
                last_exc = exc
                log.warning(
                    "agent_call_retry",
                    extra={"structured_extra": {"agent": agent, "attempt": attempt, "error": str(exc)}},
                )
                if attempt < retries:
                    await asyncio.sleep(min(2**attempt, 8))
                    continue
                break
    raise AgentClientError(agent, str(last_exc) if last_exc else "unknown error")


def _run_payload(
    *,
    job_id: str,
    dataset_path: str,
    metadata: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "job_id": job_id,
        "dataset_path": dataset_path,
        "metadata": metadata or {},
        # Compatibility aliases for older consume handlers
        "upload_id": job_id,
        "dataset_uri": dataset_path,
    }
    if extra:
        body.update(extra)
    return body


class PatternAgentClient:
    async def run(
        self,
        *,
        job_id: str,
        dataset_path: str,
        metadata: dict[str, Any] | None = None,
        mode: str | None = None,
    ) -> dict[str, Any]:
        url = f"{settings.pattern_agent_base_url.rstrip('/')}/api/v1/pattern/run"
        extra = {"mode": mode} if mode else None
        return await _post_with_retry(
            "pattern",
            url,
            _run_payload(job_id=job_id, dataset_path=dataset_path, metadata=metadata, extra=extra),
        )

    async def consume(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.run(
            job_id=str(payload.get("job_id") or payload.get("upload_id") or ""),
            dataset_path=str(payload.get("dataset_path") or payload.get("dataset_uri") or ""),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
            mode=str(payload["mode"]) if payload.get("mode") else None,
        )


class FailureAgentClient:
    async def run(
        self,
        *,
        job_id: str,
        dataset_path: str,
        metadata: dict[str, Any] | None = None,
        skip_ingest: bool | None = None,
        wait_for_modules: bool | None = None,
    ) -> dict[str, Any]:
        url = f"{settings.failure_agent_api_url.rstrip('/')}/api/v1/failure/run"
        extra: dict[str, Any] = {}
        if skip_ingest is not None:
            extra["skip_ingest"] = skip_ingest
        if wait_for_modules is not None:
            extra["wait_for_modules"] = wait_for_modules
        return await _post_with_retry(
            "failure",
            url,
            _run_payload(
                job_id=job_id,
                dataset_path=dataset_path,
                metadata=metadata,
                extra=extra or None,
            ),
        )

    async def consume(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.run(
            job_id=str(payload.get("job_id") or payload.get("upload_id") or ""),
            dataset_path=str(payload.get("dataset_path") or payload.get("dataset_uri") or ""),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
            skip_ingest=bool(payload["skip_ingest"]) if "skip_ingest" in payload else None,
            wait_for_modules=bool(payload["wait_for_modules"]) if "wait_for_modules" in payload else None,
        )


class ScanDiagnosisAgentClient:
    async def run(
        self,
        *,
        job_id: str,
        dataset_path: str,
        pattern_result_path: str | None = None,
        failure_result_path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{settings.scan_diagnosis_agent_api_url.rstrip('/')}/api/v1/scan/run"
        return await _post_with_retry(
            "scan_diagnosis",
            url,
            _run_payload(
                job_id=job_id,
                dataset_path=dataset_path,
                metadata=metadata,
                extra={
                    "pattern_result_path": pattern_result_path,
                    "failure_result_path": failure_result_path,
                    "pattern_result_uri": pattern_result_path,
                    "failure_result_uri": failure_result_path,
                },
            ),
        )

    async def consume(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self.run(
            job_id=str(payload.get("job_id") or payload.get("upload_id") or ""),
            dataset_path=str(payload.get("dataset_path") or payload.get("dataset_uri") or ""),
            pattern_result_path=payload.get("pattern_result_path") or payload.get("pattern_result_uri"),
            failure_result_path=payload.get("failure_result_path") or payload.get("failure_result_uri"),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )
