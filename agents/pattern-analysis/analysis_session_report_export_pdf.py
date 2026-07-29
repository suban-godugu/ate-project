"""Deterministic paginated PDF exporter for PA-FR-010.AS.3."""
from __future__ import annotations

import json
from io import BytesIO
from typing import Any, Mapping, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


PAGE_SIZE = landscape(A4)
LEFT = 13 * mm
RIGHT = 13 * mm
TOP = 15 * mm
BOTTOM = 16 * mm
FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"
BODY_SIZE = 6.5
HEADER_SIZE = 7
LINE_HEIGHT = 8
CELL_PAD_X = 3
CELL_PAD_Y = 2


def _format(value: Any) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (list, tuple)):
        return ", ".join(_format(item) for item in value) or "—"
    if isinstance(value, Mapping):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value)


def _safe_text(value: Any) -> str:
    return _format(value).replace("\r", " ").replace("\t", " ")


def _wrap_text(text: str, width: float, font: str, size: float) -> list[str]:
    available = max(width, 8)
    conservative_chars = max(1, int(available / (size * 0.72)))
    if "\n" not in text and len(text) <= conservative_chars:
        return [text]
    wrapped: list[str] = []
    for source in text.split("\n") or [""]:
        if not source:
            wrapped.append("")
            continue
        current = ""
        for word in source.split(" "):
            candidate = word if not current else f"{current} {word}"
            if stringWidth(candidate, font, size) <= available:
                current = candidate
                continue
            if current:
                wrapped.append(current)
                current = ""
            while word and stringWidth(word, font, size) > available:
                split_at = len(word)
                while (
                    split_at > 1
                    and stringWidth(word[:split_at], font, size) > available
                ):
                    split_at -= 1
                wrapped.append(word[:split_at])
                word = word[split_at:]
            current = word
        wrapped.append(current)
    return wrapped or [""]


class _PdfWriter:
    def __init__(self, output: BytesIO, model_hash: str) -> None:
        self.pdf = canvas.Canvas(
            output,
            pagesize=PAGE_SIZE,
            pageCompression=1,
            invariant=1,
        )
        self.pdf.setTitle("Analysis Session Quality Report")
        self.pdf.setAuthor("Pattern Analysis Agent")
        self.pdf.setSubject("PA-FR-010.AS Analysis Session Quality Report")
        self.model_hash = model_hash
        self.page_number = 1
        self.y = PAGE_SIZE[1] - TOP
        self.current_context = "Analysis Session Quality Report"
        self._body_text = self.pdf.beginText()

    @property
    def content_width(self) -> float:
        return PAGE_SIZE[0] - LEFT - RIGHT

    def _footer(self) -> None:
        self.pdf.setFillColor(colors.HexColor("#667085"))
        self.pdf.setFont(FONT, 6.5)
        self.pdf.drawString(
            LEFT,
            8 * mm,
            f"PA-FR-010.AS | Model {self.model_hash or '—'}",
        )
        self.pdf.drawRightString(
            PAGE_SIZE[0] - RIGHT,
            8 * mm,
            f"Page {self.page_number}",
        )

    def _flush_body_text(self) -> None:
        self.pdf.drawText(self._body_text)
        self._body_text = self.pdf.beginText()

    def new_page(self, context: str | None = None) -> None:
        self._flush_body_text()
        self._footer()
        self.pdf.showPage()
        self.page_number += 1
        if context is not None:
            self.current_context = context
        self.pdf.setFillColor(colors.HexColor("#667085"))
        self.pdf.setFont(FONT, 6.5)
        self.pdf.drawString(LEFT, PAGE_SIZE[1] - 9 * mm, self.current_context)
        self.y = PAGE_SIZE[1] - TOP
        self._body_text = self.pdf.beginText()

    def ensure_space(self, height: float) -> None:
        if self.y - height < BOTTOM:
            self.new_page()

    def heading(
        self,
        text: Any,
        *,
        size: float,
        color: str = "#172033",
        gap_after: float = 5,
    ) -> None:
        lines = _wrap_text(_safe_text(text), self.content_width, BOLD_FONT, size)
        height = len(lines) * (size + 3) + gap_after
        self.ensure_space(height)
        self.pdf.setFillColor(colors.HexColor(color))
        self.pdf.setFont(BOLD_FONT, size)
        for line in lines:
            self.pdf.drawString(LEFT, self.y - size, line)
            self.y -= size + 3
        self.y -= gap_after

    def message(self, value: Any, *, warning: bool = False) -> None:
        lines = _wrap_text(_safe_text(value), self.content_width - 12, FONT, 8)
        height = len(lines) * 10 + 8
        self.ensure_space(height)
        if warning:
            self.pdf.setFillColor(colors.HexColor("#fff5d9"))
            self.pdf.rect(
                LEFT,
                self.y - height,
                self.content_width,
                height,
                fill=1,
                stroke=0,
            )
            self.pdf.setFillColor(colors.HexColor("#7a4b00"))
        else:
            self.pdf.setFillColor(colors.HexColor("#172033"))
        self.pdf.setFont(FONT, 8)
        baseline = self.y - 11
        for line in lines:
            self.pdf.drawString(LEFT + 6, baseline, line)
            baseline -= 10
        self.y -= height + 3

    def _draw_header(
        self,
        columns: Sequence[str],
        widths: Sequence[float],
    ) -> None:
        height = 14
        self.pdf.setFillColor(colors.HexColor("#e9eef5"))
        self.pdf.rect(
            LEFT,
            self.y - height,
            self.content_width,
            height,
            fill=1,
            stroke=0,
        )
        self.pdf.setStrokeColor(colors.HexColor("#cbd2dc"))
        self._body_text.setFillColor(colors.HexColor("#172033"))
        self._body_text.setFont(BOLD_FONT, HEADER_SIZE)
        self._body_text.setLeading(LINE_HEIGHT)
        x = LEFT
        for column, width in zip(columns, widths):
            self.pdf.rect(x, self.y - height, width, height, fill=0, stroke=1)
            label = str(column).replace("_", " ").title()
            line = _wrap_text(
                label,
                width - 2 * CELL_PAD_X,
                BOLD_FONT,
                HEADER_SIZE,
            )[0]
            self._body_text.setTextOrigin(x + CELL_PAD_X, self.y - 10)
            self._body_text.textOut(line)
            x += width
        self.y -= height

    def table(
        self,
        title: Any,
        columns: Sequence[str],
        rows: Sequence[Mapping[str, Any]],
    ) -> None:
        self.heading(title or "Summary", size=9, gap_after=3)
        if not columns or not rows:
            self.message("No rows available.")
            return
        widths = [self.content_width / len(columns)] * len(columns)
        self.ensure_space(22)
        self._draw_header(columns, widths)

        for row in rows:
            wrapped_cells = [
                _wrap_text(
                    _safe_text(row.get(column)),
                    width - 2 * CELL_PAD_X,
                    FONT,
                    BODY_SIZE,
                )
                for column, width in zip(columns, widths)
            ]
            line_offset = 0
            total_lines = max(len(lines) for lines in wrapped_cells)
            while line_offset < total_lines:
                available_height = self.y - BOTTOM
                lines_fit = int(
                    max(0, available_height - 2 * CELL_PAD_Y) // LINE_HEIGHT
                )
                if lines_fit < 1:
                    self.new_page()
                    self._draw_header(columns, widths)
                    continue
                segment_lines = min(lines_fit, total_lines - line_offset)
                row_height = segment_lines * LINE_HEIGHT + 2 * CELL_PAD_Y
                self.pdf.setStrokeColor(colors.HexColor("#cbd2dc"))
                self.pdf.line(
                    LEFT,
                    self.y - row_height,
                    LEFT + self.content_width,
                    self.y - row_height,
                )
                self._body_text.setFillColor(colors.HexColor("#172033"))
                self._body_text.setFont(FONT, BODY_SIZE)
                self._body_text.setLeading(LINE_HEIGHT)
                x = LEFT
                for lines, width in zip(wrapped_cells, widths):
                    baseline = self.y - CELL_PAD_Y - BODY_SIZE
                    self._body_text.setTextOrigin(x + CELL_PAD_X, baseline)
                    for line in lines[line_offset : line_offset + segment_lines]:
                        self._body_text.textLine(line)
                    x += width
                self.y -= row_height
                line_offset += segment_lines
                if line_offset < total_lines:
                    self.new_page()
                    self._draw_header(columns, widths)
        self.y -= 5

    def finish(self) -> None:
        self._flush_body_text()
        self._footer()
        self.pdf.save()


def export_analysis_session_pdf(projection: Mapping[str, Any]) -> bytes:
    """Return a deterministic, paginated Analysis Session PDF."""
    output = BytesIO()
    provenance = projection.get("provenance") or {}
    validation = projection.get("validation") or {}
    writer = _PdfWriter(output, _safe_text(provenance.get("model_hash")))

    writer.heading(
        "Analysis Session Quality Report",
        size=22,
        color="#172033",
        gap_after=9,
    )
    writer.message(
        f"Generation timestamp: {_safe_text(provenance.get('generation_timestamp'))}"
    )
    writer.message(f"Model hash: {_safe_text(provenance.get('model_hash'))}")
    writer.message(f"Validation status: {_safe_text(validation.get('status'))}")

    for section in projection.get("sections") or []:
        title = _safe_text(section.get("title") or "Section")
        writer.new_page(title)
        writer.heading(
            f"{title} ({_safe_text(section.get('status') or 'Missing')})",
            size=14,
            color="#1d4ed8",
            gap_after=7,
        )
        kpis = list(section.get("kpis") or [])
        if kpis:
            writer.table(
                "Key Performance Indicators",
                ["KPI", "Value"],
                [
                    {"KPI": item.get("label"), "Value": item.get("display")}
                    for item in kpis
                ],
            )
        for message in section.get("messages") or []:
            writer.message(message, warning=True)
        for table in section.get("tables") or []:
            writer.table(
                table.get("title") or "Summary",
                list(table.get("columns") or []),
                list(table.get("rows") or []),
            )

    writer.finish()
    return output.getvalue()
