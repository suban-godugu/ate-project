"""STDF V4 binary adapter with streaming record parser (FA-FR-001)."""

from __future__ import annotations

import logging
import struct
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

from parser_engine.adapters.base import AdapterParseResult, LogAdapter
from parser_engine.adapters.schema import TestRecord

logger = logging.getLogger(__name__)

STDF_EXTENSIONS = {".stdf", ".std"}


@dataclass
class _StdfContext:
    lot_id: str = ""
    product_id: str = ""
    tester_id: str = ""
    test_stage: str = "STDF"
    wafer_id: str = ""
    die_id: str = ""
    x: int | None = None
    y: int | None = None
    hard_bin: str = ""
    soft_bin: str = ""
    pass_fail: str = "UNKNOWN"
    failing_tests: list[str] = field(default_factory=list)
    failing_patterns: list[str] = field(default_factory=list)
    parametric: dict[str, float | str] = field(default_factory=dict)


class StdfV4Adapter(LogAdapter):
    adapter_id = "stdf_v4"

    def detect(self, path: Path) -> bool:
        if path.suffix.lower() not in STDF_EXTENSIONS:
            return False
        try:
            with path.open("rb") as handle:
                header = handle.read(4)
                if len(header) < 4:
                    return False
                _, rec_typ, rec_sub = struct.unpack(">HBB", header)
                return rec_typ == 0 and rec_sub == 10
        except OSError:
            return False

    def parse(self, path: Path) -> AdapterParseResult:
        errors: list[dict[str, str]] = []
        records: list[TestRecord] = []
        ctx = _StdfContext()
        part_open = False
        record_count = 0

        try:
            with path.open("rb") as handle:
                while True:
                    header = handle.read(4)
                    if len(header) < 4:
                        break
                    rec_len, rec_typ, rec_sub = struct.unpack(">HBB", header)
                    payload_len = max(rec_len - 4, 0)
                    payload = handle.read(payload_len)
                    if len(payload) < payload_len:
                        break
                    record_count += 1
                    self._apply_record(ctx, rec_typ, rec_sub, payload, part_open)

                    if rec_typ == 1 and rec_sub == 70:
                        part_open = True
                    elif rec_typ == 5 and rec_sub == 20:
                        if part_open:
                            records.append(self._finalize_record(ctx, path))
                        part_open = False
                        ctx = _StdfContext(
                            lot_id=ctx.lot_id,
                            product_id=ctx.product_id,
                            tester_id=ctx.tester_id,
                            test_stage=ctx.test_stage,
                        )
        except (OSError, struct.error, ValueError) as exc:
            errors.append({"file": str(path), "error": str(exc)})

        if not records and record_count > 0:
            records.append(
                TestRecord(
                    lot_id=ctx.lot_id or path.stem,
                    wafer_id=ctx.wafer_id or "WAFER_UNKNOWN",
                    die_id=ctx.die_id or path.stem,
                    test_stage=ctx.test_stage,
                    tester_id=ctx.tester_id or "STDF",
                    product_id=ctx.product_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    pass_fail=ctx.pass_fail,
                    hard_bin=ctx.hard_bin,
                    soft_bin=ctx.soft_bin,
                    failing_tests=list(ctx.failing_tests),
                    failing_patterns=list(ctx.failing_patterns),
                    parametric=dict(ctx.parametric),
                    source_file=str(path),
                    adapter_id=self.adapter_id,
                )
            )
            records[-1].record_key = records[-1].build_record_key()

        return AdapterParseResult(
            records=records,
            metadata={"stdf_record_count": record_count, "parts_parsed": len(records)},
            errors=errors,
        )

    def _apply_record(
        self,
        ctx: _StdfContext,
        rec_typ: int,
        rec_sub: int,
        payload: bytes,
        part_open: bool,
    ) -> None:
        if rec_typ == 1 and rec_sub == 10:
            fields = _parse_mir(payload)
            ctx.lot_id = fields.get("lot_id", ctx.lot_id)
            ctx.product_id = fields.get("product_id", ctx.product_id)
            ctx.tester_id = fields.get("tester_id", ctx.tester_id)
            ctx.test_stage = fields.get("test_stage", ctx.test_stage)
        elif rec_typ == 1 and rec_sub == 70 and payload:
            ctx.wafer_id = _read_cn(payload, 0)[0] or ctx.wafer_id
        elif rec_typ == 5 and rec_sub == 20 and len(payload) >= 2:
            part_flag = payload[0]
            ctx.pass_fail = "PASS" if part_flag == 0 else "FAIL"
            if len(payload) >= 4:
                ctx.hard_bin = str(struct.unpack(">H", payload[2:4])[0])
        elif rec_typ == 15 and rec_sub == 10 and part_open:
            test_num, name = _parse_ptr(payload)
            ctx.failing_tests.append(name or str(test_num))
            if len(payload) >= 8:
                result = struct.unpack(">f", payload[4:8])[0]
                ctx.parametric[name or f"PTR_{test_num}"] = result
        elif rec_typ == 15 and rec_sub == 20 and part_open:
            test_num = struct.unpack(">I", payload[:4])[0] if len(payload) >= 4 else 0
            if len(payload) >= 5 and payload[4] == 0:
                ctx.failing_patterns.append(str(test_num))

    def _finalize_record(self, ctx: _StdfContext, path: Path) -> TestRecord:
        die_id = ctx.die_id or f"{ctx.wafer_id}_DIE"
        record = TestRecord(
            lot_id=ctx.lot_id or path.stem,
            wafer_id=ctx.wafer_id or "WAFER_UNKNOWN",
            die_id=die_id,
            x=ctx.x,
            y=ctx.y,
            test_stage=ctx.test_stage,
            tester_id=ctx.tester_id or "STDF",
            product_id=ctx.product_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            pass_fail=ctx.pass_fail,
            hard_bin=ctx.hard_bin,
            soft_bin=ctx.soft_bin,
            failing_tests=list(dict.fromkeys(ctx.failing_tests)),
            failing_patterns=list(dict.fromkeys(ctx.failing_patterns)),
            parametric=dict(ctx.parametric),
            source_file=str(path),
            adapter_id=self.adapter_id,
        )
        record.record_key = record.build_record_key()
        return record


def _read_cn(payload: bytes, offset: int) -> tuple[str, int]:
    if offset + 2 > len(payload):
        return "", offset
    length = struct.unpack(">H", payload[offset : offset + 2])[0]
    offset += 2
    if length == 0:
        return "", offset
    end = offset + length
    return payload[offset:end].decode("latin-1", errors="replace"), end


def _parse_mir(payload: bytes) -> dict[str, str]:
    """Extract lot / program / tester from MIR (best-effort, field-order dependent)."""
    strings: list[str] = []
    offset = 0
    while offset < len(payload):
        value, offset = _read_cn(payload, offset)
        if value:
            strings.append(value)
    result: dict[str, str] = {}
    if strings:
        result["lot_id"] = strings[0]
    if len(strings) > 1:
        result["product_id"] = strings[1]
    if len(strings) > 2:
        result["tester_id"] = strings[2]
    if len(strings) > 3:
        result["test_stage"] = strings[3]
    return result


def _parse_ptr(payload: bytes) -> tuple[int, str]:
    if len(payload) < 4:
        return 0, ""
    test_num = struct.unpack(">I", payload[:4])[0]
    name, _ = _read_cn(payload, 4)
    return test_num, name


def build_minimal_stdf_bytes(
    *,
    lot_id: str = "LOT_A",
    product_id: str = "SOC_5NM",
    tester_id: str = "V93000",
    wafer_id: str = "WF01",
    pass_fail: int = 1,
    hard_bin: int = 5,
) -> bytes:
    """Build a minimal valid STDF file for tests (FAR + MIR + PIR + PRR)."""
    chunks: list[bytes] = []

    def add_record(rec_typ: int, rec_sub: int, payload: bytes) -> None:
        rec_len = len(payload) + 4
        chunks.append(struct.pack(">HBB", rec_len, rec_typ, rec_sub) + payload)

    # FAR
    add_record(0, 10, struct.pack(">BB", 2, 2) + b"\x00\x00")

    mir_payload = b"".join(_cn(s) for s in (lot_id, product_id, tester_id, "CP"))
    add_record(1, 10, mir_payload)

    add_record(1, 70, _cn(wafer_id))

    prr_payload = bytes([pass_fail, 0]) + struct.pack(">H", hard_bin)
    add_record(5, 20, prr_payload)

    return b"".join(chunks)


def _cn(value: str) -> bytes:
    encoded = value.encode("latin-1")
    return struct.pack(">H", len(encoded)) + encoded
