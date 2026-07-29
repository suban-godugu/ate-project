"""Build a minimal STDF v4 fixture for parser tests. Run: python scripts/build_stdf_fixture.py"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ams_rw_stdf as st


def _rec(rec_typ: int, rec_sub: int, pl: dict) -> bytes:
    return st.RECORD.build({"REC_TYP": rec_typ, "REC_SUB": rec_sub, "PL": pl})


def build_sample_stdf() -> bytes:
    now = int(datetime.now(UTC).timestamp())
    chunks = [
        _rec(0, 10, {}),
        _rec(
            1,
            10,
            {
                "SETUP_T": now,
                "START_T": now,
                "STAT_NUM": 1,
                "MODE_COD": " ",
                "RTST_COD": " ",
                "PROT_COD": " ",
                "BURN_TIM": 0,
                "CMOD_COD": " ",
                "LOT_ID": "LOT-PARSER-001",
                "PART_TYP": "PROD-X1",
                "NODE_NAM": "TTR-ADV-01",
                "TSTR_TYP": "UltraFlex",
                "JOB_NAM": "SCAN_PROG_V3",
                "JOB_REV": "1.0",
                "SBLOT_ID": "",
                "OPER_NAM": "verilumen",
            },
        ),
        _rec(2, 10, {"HEAD_NUM": 1, "SITE_GRP": 1, "START_T": now, "WAFER_ID": "WAF-12"}),
        _rec(
            10,
            30,
            {
                "HEAD_NUM": 1,
                "SITE_NUM": 1,
                "TEST_TYP": "F",
                "TEST_NUM": 5001,
                "EXEC_CNT": 1,
                "FAIL_CNT": 1,
                "ALRM_CNT": 0,
                "TEST_NAM": "scan_chain_a",
                "SEQ_NAME": "",
                "TEST_LBL": "",
            },
        ),
        _rec(5, 10, {"HEAD_NUM": 1, "SITE_NUM": 1}),
        _rec(
            15,
            20,
            {
                "TEST_NUM": 5001,
                "HEAD_NUM": 1,
                "SITE_NUM": 1,
                "TEST_FLG": 128,
                "OPT_FLAG": 7,
                "CYCL_CNT": 4821,
                "REL_VADR": 0,
                "REPT_CNT": 0,
                "NUM_FAIL": 1,
                "XFAIL_AD": 10,
                "YFAIL_AD": 20,
                "VECT_OFF": 0,
                "RTN_ICNT": 0,
                "PGM_ICNT": 0,
                "RTN_INDX": [],
                "RTN_STAT": [],
                "PGM_INDX": [],
                "PGM_STAT": [],
                "FAIL_PIN": {"bitFieldLength": 0, "PL": []},
                "VECT_NAM": "P-101",
                "TIME_SET": "TS1",
                "OP_CODE": "SCAN",
                "TEST_TXT": "SC-4821",
                "PATG_NUM": 255,
                "SPIN_MAP": {"bitFieldLength": 0, "PL": []},
            },
        ),
        _rec(
            5,
            20,
            {
                "HEAD_NUM": 1,
                "SITE_NUM": 1,
                "PART_FLG": 8,
                "NUM_TEST": 1,
                "HARD_BIN": 5,
                "SOFT_BIN": 5,
                "X_COORD": 10,
                "Y_COORD": 20,
                "TEST_T": 100,
                "PART_ID": "DIE-10-20",
                "PART_TXT": "",
                "PART_FIX": "",
            },
        ),
        _rec(1, 30, {"HEAD_NUM": 1, "SITE_NUM": 1, "PART_CNT": 100, "RTST_CNT": 0, "ABRT_CNT": 0, "GOOD_CNT": 94, "FUNC_CNT": 94}),
        _rec(1, 20, {"FINISH_T": now, "DISP_COD": " ", "USR_DESC": "", "EXC_DESC": ""}),
    ]
    return b"".join(chunks)


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "sample.stdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = build_sample_stdf()
    out.write_bytes(data)
    print(f"Wrote {out} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
