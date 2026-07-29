"""Shared Parser Engine shim."""
from parser_engine.adapters.datalog_ascii import *  # noqa: F403
from parser_engine.adapters import datalog_ascii as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
