"""Build a minimal IEEE 1450 STIL 1.0 fixture for parser tests.

Run: python scripts/build_stil_fixture.py

Uses only constructs defined in IEEE Std 1450-1999 — no vendor extensions.
"""

from __future__ import annotations

from pathlib import Path

FIXTURE = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample.stil"

SAMPLE_STIL = """STIL 1.0;

Header {
  Title "VERILUMEN STIL Parser Fixture";
  Date "2026-07-06";
  Source "IEEE 1450 minimal test pattern";
}

Signals {
  clk In;
  reset In;
  scan_en In;
  scan_in In;
  scan_out Out;
}

SignalGroups {
  all_inputs = 'clk + reset + scan_en + scan_in';
  all_outputs = 'scan_out';
  all = 'clk + reset + scan_en + scan_in + scan_out';
}

Timing {
  WaveformTable wft_default {
    Period '100ns';
    Waveforms {
      clk { P { '0ns' D; '50ns' U; '80ns' D; } }
      reset { 01 { '0ns' D; } }
      scan_en { 01 { '0ns' D; } }
      scan_in { 01 { '0ns' D; } }
      scan_out { X { '0ns' X; '80ns' L/H; } }
    }
  }
}

ScanStructures {
  SC_CORE {
    ScanLength 8;
    ScanIn scan_in;
    ScanOut scan_out;
    ScanEnable scan_en;
  }
}

Pattern core_scan_pat {
  W wft_default;
  V {
    all = 10101010;
  }
}
"""


def main() -> None:
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(SAMPLE_STIL, encoding="utf-8")
    print(f"Wrote {FIXTURE} ({len(SAMPLE_STIL)} bytes)")


if __name__ == "__main__":
    main()
