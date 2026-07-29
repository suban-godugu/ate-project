"""
Backward-compatible ATE log adapter for Pattern Analysis Agent.
Implementation lives in the shared Parser Engine.
"""

from parser_engine.adapters.ate_log_adapter import *  # noqa: F403
from parser_engine.adapters import ate_log_adapter as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
