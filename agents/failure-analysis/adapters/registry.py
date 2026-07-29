"""Shared Parser Engine shim."""
from parser_engine.adapters.registry import *  # noqa: F403
from parser_engine.adapters import registry as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
