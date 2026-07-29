"""Shared Parser Engine shim."""
from parser_engine.adapters.base import *  # noqa: F403
from parser_engine.adapters import base as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
