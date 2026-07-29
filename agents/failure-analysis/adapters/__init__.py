"""Adapter package for FA-FR-001 plugin ingestion."""

from adapters.base import AdapterParseResult, IngestionReport, LogAdapter
from adapters.registry import AdapterRegistry, default_registry
from adapters.schema import SCHEMA_VERSION, TestRecord

__all__ = [
    "AdapterParseResult",
    "AdapterRegistry",
    "IngestionReport",
    "LogAdapter",
    "SCHEMA_VERSION",
    "TestRecord",
    "default_registry",
]
