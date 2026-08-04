"""ATDF stub — detect-only until full ATDF parser ships."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import BaseParserV2, DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension


class AtdfPlugin(BaseParserV2):
    parser_id = "atdf"
    extensions = {".atdf", ".atd"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions, base=0.55)
        signals = [f"ext:{path.suffix.lower()}"] if score else []
        head = read_head_text(path)
        if "ATDF" in head.upper() or "FAR:" in head:
            score += 0.25
            signals.append("header:atdf")
        return detection(self.parser_id, score, vendor="atdf", signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        return ParseOutcome(
            parser_id=self.parser_id,
            errors=[
                Issue(
                    code="ATDF_NOT_IMPLEMENTED",
                    message="ATDF parser is a detect-only stub in v2 phase A",
                    severity="error",
                )
            ],
            success=False,
            metadata={"stub": True, "source_file": str(path)},
        )


PLUGIN = AtdfPlugin()
