"""VCD / EVCD stub — detect-only until full VCD parser ships."""

from __future__ import annotations

from pathlib import Path

from parser_engine.v2.contracts import BaseParserV2, DetectionResult, Issue, ParseContext, ParseOutcome
from parser_engine.v2.plugins._common import detection, read_head_text, score_extension


class VcdPlugin(BaseParserV2):
    parser_id = "vcd"
    extensions = {".vcd", ".evcd"}

    def detect(self, path: Path, ctx: ParseContext) -> DetectionResult:
        score = score_extension(path, self.extensions, base=0.55)
        signals = [f"ext:{path.suffix.lower()}"] if score else []
        head = read_head_text(path)
        if "$date" in head or "$version" in head or "$timescale" in head:
            score += 0.3
            signals.append("header:vcd")
        if path.suffix.lower() == ".evcd":
            signals.append("format:evcd")
        return detection(self.parser_id, score, vendor="vcd", signals=signals)

    def parse(self, path: Path, ctx: ParseContext) -> ParseOutcome:
        return ParseOutcome(
            parser_id=self.parser_id,
            errors=[
                Issue(
                    code="VCD_NOT_IMPLEMENTED",
                    message="VCD/EVCD parser is a detect-only stub in v2 phase A",
                    severity="error",
                )
            ],
            success=False,
            metadata={"stub": True, "source_file": str(path)},
        )


PLUGIN = VcdPlugin()
