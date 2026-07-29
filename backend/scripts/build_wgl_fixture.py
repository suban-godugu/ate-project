"""Build a minimal TSSI WGL fixture for parser tests.

Run: python scripts/build_wgl_fixture.py

Grammar per TSSI/TSSI Waveform Generation Language (waveform … end blocks).
Reference: TDS Languages Guide — signal, timeplate, scanChain, pattern blocks.
"""

from __future__ import annotations

from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample.wgl"

SAMPLE_WGL = """waveform

! VERILUMEN WGL Parser Fixture
! Device: PROD-X1
! Tester: TTR-ADV-01
! Pattern-Group: scan-chain
! Pattern-Category: core-scan

signal
  clk : input;
  reset : input;
  scan_en : input;
  scan_in : input;
  scan_out : output;
end

timeplate wgl_default period 100ns
  clk := input[0ns:D, 50ns:S, 80ns:D];
  reset := input[0ns:D];
  scan_en := input[0ns:D];
  scan_in := input[0ns:D];
  scan_out := output[0ns:X, 80ns:Q];
end

scanChain SC_CORE
  [scan_in, scan_out];
end

pattern core_scan_pat ()
  vector(+ , wgl_default) := [0 1 0 1 0];
  vector(+ , wgl_default) := [1 0 1 0 1];
end

end
"""


def main() -> None:
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(SAMPLE_WGL, encoding="utf-8")
    print(f"Wrote {FIXTURE} ({len(SAMPLE_WGL)} bytes)")


if __name__ == "__main__":
    main()
