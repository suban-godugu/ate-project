"""
Backward-compatible STIL parser entry for Pattern Analysis Agent.
Implementation lives in the shared Parser Engine.
"""

from parser_engine.parsers.stil.pattern_stil import STILParser, STILValidationError

__all__ = ["STILParser", "STILValidationError"]
