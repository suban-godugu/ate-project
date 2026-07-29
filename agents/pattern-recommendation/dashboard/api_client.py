"""HTTP client for the Pattern Recommendation FastAPI backend."""

from __future__ import annotations

import os
from typing import Any

import httpx

DEFAULT_BASE_URL = "http://127.0.0.1:8000"
DEFAULT_TIMEOUT = 120.0


class ApiError(Exception):
    """Raised when the backend returns an error or is unreachable."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BackendClient:
    """Thin wrapper around dashboard-facing FastAPI endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = (base_url or os.getenv("DASHBOARD_API_URL") or DEFAULT_BASE_URL).rstrip(
            "/"
        )
        self.timeout = timeout

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(method, url, params=params)
        except httpx.RequestError as exc:
            raise ApiError(
                f"Cannot reach API at {self.base_url}: {exc}",
                status_code=None,
            ) from exc

        if response.status_code >= 400:
            detail = _extract_message(response)
            raise ApiError(detail, status_code=response.status_code)

        if not response.content:
            return {}
        return response.json()

    def get_health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def get_datasets_status(self) -> dict[str, Any]:
        return self._request("GET", "/datasets/status")

    def get_patterns_statistics(self) -> dict[str, Any]:
        return self._request("GET", "/patterns/statistics")

    def get_unified_summary(self) -> dict[str, Any]:
        return self._request("GET", "/recommendations/summary")

    def get_dashboard(self) -> dict[str, Any]:
        return self._request("GET", "/recommendations/dashboard")

    def refresh_recommendations(self) -> dict[str, Any]:
        return self._request("POST", "/recommendations/refresh")

    def get_failure_summary(self) -> dict[str, Any]:
        return self._request("GET", "/failures/summary")

    def refresh_failures(self) -> dict[str, Any]:
        return self._request("POST", "/failures/refresh")


def _extract_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return f"API error {response.status_code}: {response.text[:200]}"
    if isinstance(payload, dict):
        message = payload.get("message") or payload.get("detail")
        if message:
            return str(message)
    return f"API error {response.status_code}"
