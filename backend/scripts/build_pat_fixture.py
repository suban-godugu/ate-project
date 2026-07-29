"""Detection-only PAT fixture — NOT a supported vendor format.

Run: python scripts/build_pat_fixture.py

This file validates PAT routing and graceful unsupported-format handling only.
Do NOT use as a grammar reference for vendor PAT parsing.
"""

from __future__ import annotations

from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample.pat"

# Minimal text signature for content-aware detection (PAT_FILE marker)
SAMPLE_PAT = """! VERILUMEN PAT detection fixture
! NOT a supported vendor format — framework test only
! Vendor: unknown
! Generator: none
! Notes: PAT sample required for vendor grammar implementation

PAT_FILE unsupported_detection_fixture
"""


def main() -> None:
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(SAMPLE_PAT, encoding="utf-8")
    print(f"Wrote {FIXTURE} ({len(SAMPLE_PAT)} bytes)")


if __name__ == "__main__":
    main()
