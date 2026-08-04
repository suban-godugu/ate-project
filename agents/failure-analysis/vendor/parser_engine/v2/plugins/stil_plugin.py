"""STIL plugin — wraps Pattern / Failure / Diagnosis STIL parsers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from parser_engine.v2.contracts import (
    BaseParserV2,
    DetectionResult,
    Issue,
    ParseContext,
    ParseOutcome,
)
from parser_engine.v2.models.normalize import from_parser_result, from_stil_cpm
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension


class StilPlugin(BaseParserV2):
    parser_id = "stil"
    extensions = {".stil"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions)
        signals: list[str] = []
        if score:
            signals.append("ext:.stil")
        head = read_head_text(path)
        if "STIL" in head:
            score += 0.35
            signals.append("header:STIL")
        if "ScanStructures" in head or "PatternBurst" in head:
            score += 0.15
            signals.append("header:ScanStructures")
        vendor = "unknown"
        low = head.lower()
        if "tessent" in low:
            vendor = "siemens_tessent"
            signals.append("vendor:tessent")
        return detection(self.parser_id, score, vendor=vendor, signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        issues = self.validate(path, ctx)
        if any(i.severity == "error" for i in issues):
            return ParseOutcome(parser_id=self.parser_id, errors=issues, success=False)

        profile = (ctx.profile or "auto").lower()
        raw: Any
        records = []
        meta: dict[str, Any] = {}

        try:
            if profile in ("failure", "auto"):
                from parser_engine.parsers.stil.failure_stil import StilParser

                result = StilParser().parse(path)
                raw = result
                records = from_parser_result(result, parser_id=self.parser_id)
                meta = dict(getattr(result, "metadata", {}) or {})
                for err in getattr(result, "errors", []) or []:
                    issues.append(
                        Issue(code="STIL_PARSE", message=str(err.get("error") or err), severity="warning")
                    )
            elif profile == "diagnosis":
                from parser_engine.parsers.stil.diagnosis_stil import parse_stil_scan_structures

                chains = parse_stil_scan_structures(path)
                raw = chains
                meta = {"chain_count": len(chains or {})}
                # summary record
                from parser_engine.v2.models.enterprise_record import EnterpriseRecord

                er = EnterpriseRecord(
                    die_id=path.stem,
                    test_stage="STIL",
                    pass_fail="PASS" if chains else "FAIL",
                    source_file=str(path),
                    parser_id=self.parser_id,
                    parametric={"chain_count": float(len(chains or {}))},
                    raw_fields={"chains": str(list((chains or {}).keys())[:20])},
                )
                er.record_key = er.build_record_key()
                records = [er]
            else:
                from parser_engine.parsers.stil.pattern_stil import STILParser

                max_gb = float(ctx.extras.get("max_size_gb", 10.0))
                cpm = STILParser().parse(str(path), max_size_gb=max_gb)
                raw = cpm
                records = from_stil_cpm(cpm, source_file=str(path), parser_id=self.parser_id)
                meta = dict((cpm or {}).get("metadata") or {})
        except Exception as exc:  # noqa: BLE001
            return ParseOutcome(
                parser_id=self.parser_id,
                errors=issues + [Issue(code="STIL_EXCEPTION", message=str(exc))],
                success=False,
            )

        outcome = ParseOutcome(
            parser_id=self.parser_id,
            records=records,
            errors=issues,
            metadata=meta,
            raw=raw,
            success=True,
        )
        outcome.metadata.update(self.metadata(path, outcome))
        return outcome


PLUGIN = StilPlugin()
