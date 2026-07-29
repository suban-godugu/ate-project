"""Shared Parser Engine shim — Scan Diagnosis STIL / topology parser."""
from parser_engine.parsers.stil.diagnosis_stil import *  # noqa: F403
from parser_engine.parsers.stil import diagnosis_stil as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
