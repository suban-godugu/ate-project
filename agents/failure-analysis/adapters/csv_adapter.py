"""Shared Parser Engine shim."""
from parser_engine.adapters.csv_adapter import *  # noqa: F403
from parser_engine.adapters import csv_adapter as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
