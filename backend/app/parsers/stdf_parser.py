from __future__ import annotations

import io
from dataclasses import dataclass, field


@dataclass
class StdfFailure:
    chain_id: str
    pattern_id: str | None
    chip: str | None
    fail_cycle: int | None
    fail_type: str
    root_cause: str


@dataclass
class StdfWaferResult:
    wafer_id: str | None
    part_cnt: int | None
    good_cnt: int | None
    yield_pct: float | None


@dataclass
class StdfParseResult:
    lot_id: str | None = None
    product_code: str | None = None
    tester_code: str | None = None
    test_program: str | None = None
    wafer_results: list[StdfWaferResult] = field(default_factory=list)
    failures: list[StdfFailure] = field(default_factory=list)
    patterns: set[str] = field(default_factory=set)
    total_parts: int = 0
    good_parts: int = 0
    yield_pct: float | None = None
    raw_record_counts: dict[str, int] = field(default_factory=dict)


def _norm_code(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _is_ftr_fail(test_flg: int) -> bool:
    # STDF TEST_FLG bit 7 = fail
    return bool(test_flg & 0x80)


def _fail_type_from_ftr(op_code: str | None, test_txt: str | None) -> str:
    text = " ".join(filter(None, [op_code, test_txt])).lower()
    if "hold" in text:
        return "hold"
    if "transition" in text or "scan" in text:
        return "transition"
    if "stuck" in text:
        return "stuck-at"
    return "functional"


def _chain_id_from_ftr(test_txt: str | None, test_num: int | None, cycl_cnt: int | None) -> str:
    if test_txt and test_txt.strip().upper().startswith("SC-"):
        return test_txt.strip().split()[0]
    if test_txt and test_txt.strip():
        token = test_txt.strip().split()[0]
        if len(token) <= 32:
            return token
    if cycl_cnt is not None:
        return f"SC-{cycl_cnt}"
    if test_num is not None:
        return f"SC-{test_num}"
    return "SC-UNKNOWN"


def _pl_get(pl, name: str, default=None):
    if pl is None:
        return default
    if isinstance(pl, dict):
        return pl.get(name, default)
    return getattr(pl, name, default)


def _parse_wrr_raw(raw: bytes) -> dict | None:
    if len(raw) < 4 or raw[2] != 2 or raw[3] != 20:
        return None
    import struct

    pl = raw[4:]
    if len(pl) < 30:
        return None
    head, site, finish_t, part_cnt, rtst, abrt, good, func = struct.unpack_from("<BBIIIIII", pl)
    return {
        "REC_TYP": 2,
        "REC_SUB": 20,
        "PL": {
            "HEAD_NUM": head,
            "SITE_GRP": site,
            "FINISH_T": finish_t,
            "PART_CNT": part_cnt,
            "RTST_CNT": rtst,
            "ABRT_CNT": abrt,
            "GOOD_CNT": good,
            "FUNC_CNT": func,
        },
    }


def _iter_stdf_records(data: bytes):
    import ams_rw_stdf as st

    known = st._dict_of_payloads
    stream = io.BufferedReader(io.BytesIO(data))
    while True:
        try:
            raw = st.get_record_bytes(stream)
        except EOFError:
            break
        rec_typ = raw[2]
        rec_sub = raw[3]
        key = rec_typ << 8 | rec_sub
        if key == (2 << 8 | 20):
            wrr = _parse_wrr_raw(raw)
            if wrr:
                yield wrr
            continue
        if key not in known:
            continue
        try:
            parsed = st.RECORD.parse(raw)
            yield {"REC_TYP": parsed.REC_TYP, "REC_SUB": parsed.REC_SUB, "PL": parsed.PL}
        except Exception:
            continue


def parse_stdf_bytes(data: bytes) -> StdfParseResult:
    result = StdfParseResult()
    current_wafer: str | None = None
    current_x: int | None = None
    current_y: int | None = None

    for rec in _iter_stdf_records(data):
        rec_typ = rec["REC_TYP"]
        rec_sub = rec["REC_SUB"]
        key = f"{rec_typ}:{rec_sub}"
        result.raw_record_counts[key] = result.raw_record_counts.get(key, 0) + 1
        pl = rec["PL"]

        if rec_typ == 1 and rec_sub == 10:
            result.lot_id = _norm_code(_pl_get(pl, "LOT_ID"))
            result.product_code = _norm_code(_pl_get(pl, "PART_TYP"))
            result.tester_code = _norm_code(_pl_get(pl, "NODE_NAM") or _pl_get(pl, "TSTR_TYP"))
            result.test_program = _norm_code(_pl_get(pl, "JOB_NAM"))

        elif rec_typ == 2 and rec_sub == 10:
            current_wafer = _norm_code(_pl_get(pl, "WAFER_ID"))

        elif rec_typ == 2 and rec_sub == 20:
            part_cnt = int(_pl_get(pl, "PART_CNT", 0) or 0)
            good_cnt = int(_pl_get(pl, "GOOD_CNT", 0) or 0)
            yld = round(good_cnt / part_cnt * 100, 2) if part_cnt else None
            result.wafer_results.append(
                StdfWaferResult(
                    wafer_id=current_wafer,
                    part_cnt=part_cnt or None,
                    good_cnt=good_cnt or None,
                    yield_pct=yld,
                )
            )
            result.total_parts += part_cnt
            result.good_parts += good_cnt
            current_wafer = None

        elif rec_typ == 1 and rec_sub == 30:
            part_cnt = int(_pl_get(pl, "PART_CNT", 0) or 0)
            good_cnt = int(_pl_get(pl, "GOOD_CNT", 0) or 0)
            if part_cnt:
                yld = round(good_cnt / part_cnt * 100, 2)
                result.wafer_results.append(
                    StdfWaferResult(
                        wafer_id=current_wafer,
                        part_cnt=part_cnt,
                        good_cnt=good_cnt,
                        yield_pct=yld,
                    )
                )
                result.total_parts += part_cnt
                result.good_parts += good_cnt

        elif rec_typ == 5 and rec_sub == 20:
            current_x = _pl_get(pl, "X_COORD")
            current_y = _pl_get(pl, "Y_COORD")

        elif rec_typ == 15 and rec_sub == 20:
            test_flg = int(_pl_get(pl, "TEST_FLG", 0) or 0)
            if not _is_ftr_fail(test_flg):
                continue
            vect_nam = _norm_code(_pl_get(pl, "VECT_NAM"))
            test_txt = _norm_code(_pl_get(pl, "TEST_TXT"))
            cycl_cnt = _pl_get(pl, "CYCL_CNT")
            test_num = _pl_get(pl, "TEST_NUM")
            op_code = _norm_code(_pl_get(pl, "OP_CODE"))
            chain_id = _chain_id_from_ftr(test_txt, test_num, cycl_cnt)
            pattern_id = vect_nam or (f"P-{test_num}" if test_num is not None else None)
            if pattern_id:
                result.patterns.add(pattern_id)
            chip = None
            if current_x is not None and current_y is not None:
                chip = f"M{current_x}-{current_y}"
            result.failures.append(
                StdfFailure(
                    chain_id=chain_id,
                    pattern_id=pattern_id,
                    chip=chip,
                    fail_cycle=int(cycl_cnt) if cycl_cnt is not None else None,
                    fail_type=_fail_type_from_ftr(op_code, test_txt),
                    root_cause=f"STDF FTR fail — {test_txt or op_code or chain_id}",
                )
            )

        elif rec_typ == 15 and rec_sub == 10:
            test_flg = int(_pl_get(pl, "TEST_FLG", 0) or 0)
            if not _is_ftr_fail(test_flg):
                continue
            test_txt = _norm_code(_pl_get(pl, "TEST_TXT"))
            test_num = _pl_get(pl, "TEST_NUM")
            result_num = _pl_get(pl, "RESULT")
            pattern_id = test_txt or (f"P-{test_num}" if test_num is not None else None)
            if pattern_id:
                result.patterns.add(pattern_id)
            chain_id = f"SC-{test_num}" if test_num is not None else "SC-PTR"
            result.failures.append(
                StdfFailure(
                    chain_id=chain_id,
                    pattern_id=pattern_id,
                    chip=None,
                    fail_cycle=int(result_num) if isinstance(result_num, (int, float)) else None,
                    fail_type="parametric",
                    root_cause=f"STDF PTR fail — {test_txt or chain_id}",
                )
            )

    if result.total_parts:
        result.yield_pct = round(result.good_parts / result.total_parts * 100, 2)
    elif result.wafer_results:
        last = result.wafer_results[-1]
        result.yield_pct = last.yield_pct

    return result
