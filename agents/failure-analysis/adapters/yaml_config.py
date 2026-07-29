"""Shared Parser Engine shim."""
from parser_engine.adapters.yaml_config import *  # noqa: F403
from parser_engine.adapters import yaml_config as _mod

__all__ = [name for name in dir(_mod) if not name.startswith("_")]
