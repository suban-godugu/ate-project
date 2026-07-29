# -*- coding: utf-8 -*-
"""Convert markdown prompt archive to PDF using fpdf2."""
import sys
import textwrap
import subprocess
from pathlib import Path

try:
    from fpdf import FPDF
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2", "-q"])
    from fpdf import FPDF


def sanitize(text: str) -> str:
    text = text.replace("\t", "    ")
    return text.encode("latin-1", "replace").decode("latin-1")


def wrap(text: str, width: int = 110) -> str:
    if not text.strip():
        return ""
    parts = []
    for segment in text.split("\n"):
        segment = segment.strip()
        if not segment:
            parts.append("")
            continue
        if len(segment) <= width:
            parts.append(segment)
        else:
            parts.extend(textwrap.wrap(segment, width=width, break_long_words=True, break_on_hyphens=True))
    return "\n".join(parts)


class PromptPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "VERILUMEN / COMPTY - Complete Prompt Archive", align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def footer(self):
        self.set_y(-10)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 8, f"Page {self.page_no()}", align="C")


def write_block(pdf: PromptPDF, text: str, size: float, style: str = "", lh: float = 5):
    pdf.set_font("Helvetica", style, size)
    content = wrap(sanitize(text))
    if not content.strip():
        pdf.ln(lh)
        return
    pdf.multi_cell(pdf.epw, lh, content)


def convert(md_path: Path, pdf_path: Path):
    text = md_path.read_text(encoding="utf-8")
    pdf = PromptPDF(orientation="P", unit="mm", format="A4")
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.add_page()
    in_code = False
    code_buf: list[str] = []

    for raw in text.splitlines():
        line = raw.rstrip()

        if line.strip().startswith("```"):
            if in_code:
                block = "\n".join(code_buf)
                pdf.set_fill_color(245, 245, 245)
                write_block(pdf, block, 8, "", 4.2)
                code_buf = []
                in_code = False
                pdf.ln(2)
            else:
                in_code = True
            continue

        if in_code:
            code_buf.append(line)
            continue

        if line.startswith("# "):
            pdf.ln(3)
            write_block(pdf, line[2:], 16, "B", 7)
        elif line.startswith("## "):
            pdf.ln(2)
            write_block(pdf, line[3:], 12, "B", 6)
        elif line.startswith("### "):
            pdf.ln(1)
            write_block(pdf, line[4:], 10, "B", 5)
        elif line.strip() == "---":
            pdf.ln(2)
        elif line.startswith("|") and "---" not in line:
            write_block(pdf, line, 8, "", 4.5)
        elif line.strip():
            write_block(pdf, line, 9, "", 4.5)
        else:
            pdf.ln(1)

    pdf.output(str(pdf_path))
    print("Wrote:", pdf_path)


if __name__ == "__main__":
    convert(Path(sys.argv[1]), Path(sys.argv[2]))
