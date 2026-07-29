"""Pattern ID normalization helpers."""

from __future__ import annotations

import re

_PATTERN_RE = re.compile(r"(?i)^p(?:attern)?[_-]?(\d+)$")


def normalize_pattern_id(raw: object) -> str:
    """
    Normalize pattern identifiers to a canonical form.

    Examples
    --------
    P1, p1, Pattern_1, Pattern-1 -> Pattern_1
    """
    if raw is None:
        return ""
    token = str(raw).strip()
    if not token:
        return ""
    match = _PATTERN_RE.match(token)
    if match:
        return f"Pattern_{int(match.group(1))}"
    return token
