"""STDF plugin wrapping v1 StdfParser / StdfV4Adapter path."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import BaseParserV2, DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.models.normalize import from_parser_result
from parser_engine.v2.plugins._common import detection, read_head_bytes, score_extension


class StdfPlugin(BaseParserV2):
    parser_id = "stdf"
    extensions = {".stdf", ".std"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions, base=0.5)
        signals: list[str] = []
        if score:
            signals.append(f"ext:{path.suffix.lower()}")
        head = read_head_bytes(path, 8)
        # STDF FAR typically starts with record length + type/subtype; heuristic only
        if head and len(head) >= 4:
            score += 0.2
            signals.append("binary:header")
        return detection(self.parser_id, score, vendor="stdf_v4", signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        issues = self.validate(path, ctx)
        if any(i.severity == "error" for i in issues):
            return ParseOutcome(parser_id=self.parser_id, errors=issues, success=False)
        try:
            from parser_engine.parsers.stdf.stdf_parser import StdfParser

            result = StdfParser().parse(path)
            records = from_parser_result(result, parser_id=self.parser_id)
            for err in getattr(result, "errors", []) or []:
                issues.append(Issue(code="STDF_PARSE", message=str(err.get("error") or err), severity="warning"))
            return ParseOutcome(
                parser_id=self.parser_id,
                records=records,
                errors=issues,
                metadata=dict(getattr(result, "metadata", {}) or {}),
                raw=result,
                success=True,
            )
        except Exception as exc:  # noqa: BLE001
            return ParseOutcome(
                parser_id=self.parser_id,
                errors=issues + [Issue(code="STDF_EXCEPTION", message=str(exc))],
                success=False,
            )


PLUGIN = StdfPlugin()
