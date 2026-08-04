"""ASCII / generic datalog plugin wrapping v1 AsciiParser."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import BaseParserV2, DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.models.normalize import from_parser_result
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension


class AsciiPlugin(BaseParserV2):
    parser_id = "ascii"
    extensions = {".txt", ".dat", ".log"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        # Lower priority than ate_log for .log files
        score = score_extension(path, self.extensions, base=0.2)
        signals = [f"ext:{path.suffix.lower()}"] if score else []
        head = read_head_text(path)
        if "LOT" in head.upper() and "DIE" in head.upper():
            score += 0.2
            signals.append("header:lot_die")
        return detection(self.parser_id, score, signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        issues = self.validate(path, ctx)
        if any(i.severity == "error" for i in issues):
            return ParseOutcome(parser_id=self.parser_id, errors=issues, success=False)
        try:
            from parser_engine.parsers.ascii.ascii_parser import AsciiParser

            result = AsciiParser().parse(path)
            return ParseOutcome(
                parser_id=self.parser_id,
                records=from_parser_result(result, parser_id=self.parser_id),
                errors=issues,
                metadata=dict(getattr(result, "metadata", {}) or {}),
                raw=result,
                success=True,
            )
        except Exception as exc:  # noqa: BLE001
            return ParseOutcome(
                parser_id=self.parser_id,
                errors=issues + [Issue(code="ASCII_EXCEPTION", message=str(exc))],
                success=False,
            )


PLUGIN = AsciiPlugin()
