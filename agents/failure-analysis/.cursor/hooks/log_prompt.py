#!/usr/bin/env python3
"""Project-level prompt logger for Failure-Analysis-Agent."""
from __future__ import annotations

import os
import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
USER_HOOK = Path.home() / ".cursor" / "hooks" / "log_prompt.py"


def main() -> int:
    os.environ["PROMPT_LOG_ROOT"] = str(PROJECT_ROOT)
    target = USER_HOOK if USER_HOOK.exists() else Path(__file__).resolve()
    spec = spec_from_file_location("prompt_logger", target)
    if spec is None or spec.loader is None:
        print('{"permission": "allow"}')
        return 0
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return int(module.main())


if __name__ == "__main__":
    raise SystemExit(main())
