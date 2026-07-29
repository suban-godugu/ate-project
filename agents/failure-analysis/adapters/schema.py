"""Shared Parser Engine shim."""
from parser_engine.adapters.schema import *  # noqa: F403
from parser_engine.adapters import schema as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
