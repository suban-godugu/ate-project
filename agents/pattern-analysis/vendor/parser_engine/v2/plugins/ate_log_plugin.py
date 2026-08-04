"""ATE / LOG plugin — wraps Pattern ATE, Diagnosis ATE, and Failure ASCII paths."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from parser_engine.v2.contracts import (
    BaseParserV2,
    DetectionResult,
    Issue,
    ParseContext,
    ParseOutcome,
)
from parser_engine.v2.models.enterprise_record import EnterpriseRecord
from parser_engine.v2.models.normalize import (
    from_diagnosis_dataframe,
    from_parser_result,
    from_pattern_ate_map,
)
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension
from parser_engine.v2.streaming.reader import iter_lines


class AteLogPlugin(BaseParserV2):
    parser_id = "ate_log"
    extensions = {".log", ".txt", ".dat"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions, base=0.35)
        signals: list[str] = []
        if score:
            signals.append(f"ext:{path.suffix.lower()}")
        head = read_head_text(path, 8192)
        vendor = "unknown"
        if "EXPECTED_OUTPUT" in head and "|" in head:
            score += 0.4
            signals.append("header:EXPECTED_OUTPUT")
            vendor = "verilumen"
        if "[PATTERN_ID" in head or "PATTERN_ID" in head:
            score += 0.25
            signals.append("header:PATTERN_ID")
        low = head.lower()
        for key, name in (
            ("tessent", "siemens_tessent"),
            ("advantest", "advantest"),
            ("teradyne", "teradyne"),
            ("cohu", "cohu"),
            ("verigy", "verigy"),
            ("national instruments", "ni"),
        ):
            if key in low:
                vendor = name
                score += 0.1
                signals.append(f"vendor:{name}")
                break
        return detection(self.parser_id, score, vendor=vendor, signals=signals)

    def supports_streaming(self) -> bool:
        return True

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        issues = self.validate(path, ctx)
        if any(i.severity == "error" for i in issues):
            return ParseOutcome(parser_id=self.parser_id, errors=issues, success=False)

        profile = (ctx.profile or "auto").lower()
        try:
            if profile == "pattern":
                from parser_engine.parsers.ate.pattern_ate import ATEParser

                raw = ATEParser().parse(str(path))
                records = from_pattern_ate_map(raw, source_file=str(path), parser_id=self.parser_id)
            elif profile == "diagnosis":
                from parser_engine.parsers.ate.diagnosis_ate import parse_log_to_dataframe

                # Default keeps FAIL for diagnosis. Good-die logs are all PASS
                # (STATUS:P) — fall back so upload parse does not return empty.
                keep = str(ctx.extras.get("keep_status") or "FAIL")
                df = parse_log_to_dataframe(path, keep_status=keep)
                if getattr(df, "empty", True):
                    df = parse_log_to_dataframe(path, keep_status="PASS")
                if getattr(df, "empty", True):
                    df = parse_log_to_dataframe(path, keep_status="ALL")
                raw = df
                records = from_diagnosis_dataframe(df, source_file=str(path), parser_id=self.parser_id)
            else:
                from parser_engine.parsers.ascii.ascii_parser import AsciiParser

                result = AsciiParser().parse(path)
                raw = result
                records = from_parser_result(result, parser_id=self.parser_id)
                for err in getattr(result, "errors", []) or []:
                    issues.append(
                        Issue(code="ATE_PARSE", message=str(err.get("error") or err), severity="warning")
                    )
        except Exception as exc:  # noqa: BLE001
            return ParseOutcome(
                parser_id=self.parser_id,
                errors=issues + [Issue(code="ATE_EXCEPTION", message=str(exc))],
                success=False,
            )

        outcome = ParseOutcome(
            parser_id=self.parser_id,
            records=records,
            errors=issues,
            raw=raw,
            metadata=self.metadata(path, ParseOutcome(parser_id=self.parser_id, records=records)),
            success=True,
        )
        return outcome

    def stream(self, path: Path, ctx: ParseContext) -> Iterator[EnterpriseRecord]:
        # Lightweight streaming of FAIL-ish lines for huge logs; full semantics via parse().
        start = max(0, int(ctx.resume_line or 0))
        for lineno, line in iter_lines(path, start_line=start):
            upper = line.upper()
            if "STATUS" in upper and ("FAIL" in upper or upper.strip().endswith(":F")):
                er = EnterpriseRecord(
                    test_stage="ATE",
                    pass_fail="FAIL",
                    source_file=str(path),
                    parser_id=self.parser_id,
                    raw_fields={"line": line.strip(), "line_no": str(lineno)},
                    parse_confidence=0.4,
                )
                er.record_key = er.build_record_key()
                yield er


PLUGIN = AteLogPlugin()
