"""CSV plugin wrapping v1 CsvParser."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import BaseParserV2, DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.models.normalize import from_parser_result
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension


class CsvPlugin(BaseParserV2):
    parser_id = "csv"
    extensions = {".csv"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions)
        signals = ["ext:.csv"] if score else []
        head = read_head_text(path, 1024)
        if "," in head and ("lot" in head.lower() or "die" in head.lower()):
            score += 0.25
            signals.append("header:csv_die_like")
        return detection(self.parser_id, score, signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        issues = self.validate(path, ctx)
        if any(i.severity == "error" for i in issues):
            return ParseOutcome(parser_id=self.parser_id, errors=issues, success=False)
        try:
            from parser_engine.parsers.csv.csv_parser import CsvParser

            result = CsvParser().parse(path)
            return ParseOutcome(
                parser_id=self.parser_id,
                records=from_parser_result(result, parser_id=self.parser_id),
                errors=issues
                + [
                    Issue(code="CSV_PARSE", message=str(e.get("error") or e), severity="warning")
                    for e in (getattr(result, "errors", []) or [])
                ],
                metadata=dict(getattr(result, "metadata", {}) or {}),
                raw=result,
                success=True,
            )
        except Exception as exc:  # noqa: BLE001
            return ParseOutcome(
                parser_id=self.parser_id,
                errors=issues + [Issue(code="CSV_EXCEPTION", message=str(exc))],
                success=False,
            )


PLUGIN = CsvPlugin()
