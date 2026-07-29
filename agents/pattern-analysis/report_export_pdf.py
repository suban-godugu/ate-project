"""Memory-efficient paginated PDF exporter for PA-FR-010.3.

The renderer writes rows directly to a ReportLab canvas. It avoids building a
large Platypus flowable graph, so memory and layout time grow linearly with the
number of report rows.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any, Mapping, Sequence

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from report_presentation_builder import format_cell_value

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


def _safe_text(value: Any) -> str:
    return format_cell_value(value).replace("\r", " ").replace("\t", " ")


def _wrap_text(text: str, width: float, font: str, size: float) -> list[str]:
    """Wrap text deterministically without dropping characters."""
    available = max(width, 8)
    conservative_chars = max(1, int(available / (size * 0.72)))
    if "\n" not in text and len(text) <= conservative_chars:
        return [text]
    source_lines = text.split("\n") or [""]
    wrapped: list[str] = []
    for source in source_lines:
        if not source:
            wrapped.append("")
            continue
        words = source.split(" ")
        current = ""
        for word in words:
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


def _chart_table(
    chart: Mapping[str, Any],
) -> tuple[list[str], list[Mapping[str, Any]]]:
    data = chart.get("data")
    if isinstance(data, Mapping):
        return (
            ["label", "value"],
            [
                {"label": key, "value": value}
                for key, value in sorted(data.items(), key=lambda item: str(item[0]))
            ],
        )
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        rows = [item for item in data if isinstance(item, Mapping)]
        columns: list[str] = []
        for row in rows:
            for key in row:
                if key not in columns:
                    columns.append(str(key))
        return columns, rows
    return [], []


class _PdfWriter:
    def __init__(self, output: BytesIO, model_hash: str) -> None:
        self.pdf = canvas.Canvas(
            output,
            pagesize=PAGE_SIZE,
            pageCompression=1,
            invariant=1,
        )
        self.pdf.setTitle("Pattern Quality Report")
        self.pdf.setAuthor("Pattern Analysis Agent")
        self.pdf.setSubject("PA-FR-010 Single Log Pattern Quality Report")
        self.model_hash = model_hash
        self.page_number = 1
        self.y = PAGE_SIZE[1] - TOP
        self.current_context = "Pattern Quality Report"
        self._body_text = self.pdf.beginText()

    @property
    def content_width(self) -> float:
        return PAGE_SIZE[0] - LEFT - RIGHT

    def _footer(self) -> None:
        self.pdf.setFillColor(colors.HexColor("#667085"))
        self.pdf.setFont(FONT, 6.5)
        footer_hash = self.model_hash or "—"
        self.pdf.drawString(
            LEFT,
            8 * mm,
            f"PA-FR-010 | Model {footer_hash}",
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

    def ensure_space(self, height: float, context: str | None = None) -> None:
        if self.y - height < BOTTOM:
            self.new_page(context)

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
        text = _safe_text(value)
        lines = _wrap_text(text, self.content_width - 12, FONT, 8)
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
        self.pdf.rect(LEFT, self.y - height, self.content_width, height, fill=1, stroke=0)
        self.pdf.setStrokeColor(colors.HexColor("#cbd2dc"))
        self.pdf.setFillColor(colors.HexColor("#172033"))
        self._body_text.setFillColor(colors.HexColor("#172033"))
        self._body_text.setFont(BOLD_FONT, HEADER_SIZE)
        self._body_text.setLeading(LINE_HEIGHT)
        x = LEFT
        for column, width in zip(columns, widths):
            self.pdf.rect(x, self.y - height, width, height, fill=0, stroke=1)
            label = str(column).replace("_", " ").title()
            lines = _wrap_text(label, width - 2 * CELL_PAD_X, BOLD_FONT, HEADER_SIZE)
            self._body_text.setTextOrigin(x + CELL_PAD_X, self.y - 10)
            self._body_text.textOut(lines[0])
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
                    self.new_page(self.current_context)
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
                    self.new_page(self.current_context)
                    self._draw_header(columns, widths)
        self.y -= 5

    def finish(self) -> None:
        self._flush_body_text()
        self._footer()
        self.pdf.save()


def export_pdf(presentation: Mapping[str, Any]) -> bytes:
    """Return a complete, linearly-rendered PDF report."""
    output = BytesIO()
    provenance = presentation.get("provenance") or {}
    validation = presentation.get("validation") or {}
    writer = _PdfWriter(output, _safe_text(provenance.get("model_hash")))

    writer.heading("Pattern Quality Report", size=22, color="#172033", gap_after=9)
    writer.message(
        f"Generation timestamp: {_safe_text(provenance.get('generation_timestamp'))}"
    )
    writer.message(f"Model hash: {_safe_text(provenance.get('model_hash'))}")
    writer.message(f"Validation status: {_safe_text(validation.get('status'))}")

    for section in presentation.get("sections") or []:
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
                    {
                        "KPI": item.get("label"),
                        "Value": item.get("display"),
                    }
                    for item in kpis
                ],
            )
        for message in section.get("messages") or []:
            writer.message(message, warning=True)
        for chart in section.get("charts") or []:
            columns, rows = _chart_table(chart)
            if columns:
                writer.table(
                    f"Chart Data: {chart.get('title') or 'Chart'}",
                    columns,
                    rows,
                )
        for table_model in section.get("tables") or []:
            writer.table(
                table_model.get("title") or "Summary",
                list(table_model.get("columns") or []),
                list(table_model.get("rows") or []),
            )

    writer.finish()
    return output.getvalue()
