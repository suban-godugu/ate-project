"""JSON plugin wrapping v1 JsonParser."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import BaseParserV2, DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.models.normalize import from_parser_result
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension


class JsonPlugin(BaseParserV2):
    parser_id = "json"
    extensions = {".json"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions)
        signals = ["ext:.json"] if score else []
        head = read_head_text(path, 256).lstrip()
        if head.startswith("{") or head.startswith("["):
            score += 0.3
            signals.append("header:json")
        return detection(self.parser_id, score, signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        issues = self.validate(path, ctx)
        if any(i.severity == "error" for i in issues):
            return ParseOutcome(parser_id=self.parser_id, errors=issues, success=False)
        try:
            from parser_engine.parsers.json.json_parser import JsonParser

            result = JsonParser().parse(path)
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
                errors=issues + [Issue(code="JSON_EXCEPTION", message=str(exc))],
                success=False,
            )


PLUGIN = JsonPlugin()
