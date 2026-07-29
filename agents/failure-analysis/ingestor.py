"""Shared Parser Engine shim — ATE log ingestor."""
from parser_engine.parsers.ate.ingestor import *  # noqa: F403
from parser_engine.parsers.ate import ingestor as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
