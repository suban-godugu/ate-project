"""WGL stub — detect-only until full Waveform Generation Language parser ships."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import BaseParserV2, DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension


class WglPlugin(BaseParserV2):
    parser_id = "wgl"
    extensions = {".wgl"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions, base=0.55)
        signals = ["ext:.wgl"] if score else []
        head = read_head_text(path)
        if "waveform" in head.lower() or "WGL" in head:
            score += 0.25
            signals.append("header:wgl")
        return detection(self.parser_id, score, vendor="wgl", signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        return ParseOutcome(
            parser_id=self.parser_id,
            errors=[
                Issue(
                    code="WGL_NOT_IMPLEMENTED",
                    message="WGL parser is a detect-only stub in v2 phase A",
                    severity="error",
                )
            ],
            success=False,
            metadata={"stub": True, "source_file": str(path)},
        )


PLUGIN = WglPlugin()
