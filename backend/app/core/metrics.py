"""Prometheus metrics for VERILUMEN API and workers."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUESTS = Counter(
    "verilumen_http_requests_total",
    "Total HTTP requests",
    ["method", "route", "status"],
)
HTTP_DURATION = Histogram(
    "verilumen_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "route"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)
HTTP_RESPONSE_BYTES = Histogram(
    "verilumen_http_response_bytes",
    "HTTP response body size",
    ["method", "route"],
    buckets=(100, 1000, 10000, 100000, 1000000),
)

UPLOAD_TOTAL = Counter("verilumen_uploads_total", "Upload jobs completed", ["status", "kind"])
UPLOAD_DURATION = Histogram(
    "verilumen_upload_duration_seconds",
    "Upload pipeline duration",
    ["kind"],
    buckets=(1, 5, 10, 30, 60, 120, 300, 600),
)
PARSER_DURATION = Histogram(
    "verilumen_parser_duration_seconds",
    "Parser step duration",
    ["format"],
    buckets=(0.1, 0.5, 1, 2, 5, 10, 30, 60),
)
FAILED_UPLOADS = Counter("verilumen_failed_uploads_total", "Failed upload jobs", ["kind"])

CACHE_HITS = Counter("verilumen_cache_hits_total", "Redis cache hits", ["key_prefix"])
CACHE_MISSES = Counter("verilumen_cache_misses_total", "Redis cache misses", ["key_prefix"])

WORKER_JOBS = Counter("verilumen_worker_jobs_total", "ARQ worker jobs processed", ["job", "status"])

RECOMMENDATION_COUNT = Gauge("verilumen_recommendations_total", "Recommendations in database")
ALERT_COUNT = Gauge("verilumen_alerts_total", "Alerts in database")
