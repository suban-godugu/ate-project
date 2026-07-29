"""Shared Parser Engine shim — STIL ingestor."""
from parser_engine.parsers.stil.stil_ingestor import *  # noqa: F403
from parser_engine.parsers.stil import stil_ingestor as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
