#!/usr/bin/env python3
"""
Generalised Daily Briefing PDF Builder for Hermes Agent.

Usage:
    python3 build_briefing.py config.json output.pdf

Config JSON format:
{
  "date": "26 August 2026",
  "title": "Your Briefing Title",
  "sections": [
    ["Section Headline", "Body text... Multiple paragraphs separated by \\n."]
  ],
  "sources": [
    ["Source Name", "https://url"],
    ...
  ],
  "style": {
    "header_bg": [10, 12, 20],
    "accent_color": [0, 255, 140],
    "font_family": "Helvetica",
    "header_text_color": [255, 255, 255]
  }
}
"""

import sys, json, os
from fpdf import FPDF


class BriefingPDF(FPDF):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.style = data.get("style", {})

    def header(self):
        if self.page_no() > 1:
            return
        style = self.style
        bg = style.get("header_bg", [10, 12, 20])
        accent = style.get("accent_color", [0, 255, 140])
        font = style.get("font_family", "Helvetica")
        text_color = style.get("header_text_color", [255, 255, 255])

        # Dark banner
        self.set_fill_color(*bg)
        self.rect(0, 0, 210, 40, "F")

        # Title
        self.set_y(8)
        self.set_font(font, "B", 16)
        self.set_text_color(*text_color)
        self.cell(0, 9, self.data.get("title", "Briefing")[:95],
                  new_x="LMARGIN", new_y="NEXT")

        # Date line
        self.set_font(font, "", 10)
        self.set_text_color(*accent)
        self.cell(0, 6, self.data.get("date", ""),
                  new_x="LMARGIN", new_y="NEXT")

        # Divider
        self.set_draw_color(*accent)
        self.set_y(43)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())

        # Reset body position
        self.set_y(48)

    def footer(self):
        self.set_y(-15)
        self.set_font(self.style.get("font_family", "Helvetica"), "I", 8)
        self.set_text_color(120)
        self.cell(0, 10, f"[ page {self.page_no()} ]", align="C")


def build_pdf(data, output_path, batch_mode=False):
    """Generate a PDF from briefing data JSON."""
    pdf = BriefingPDF(data)
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    font = data.get("style", {}).get("font_family", "Helvetica")
    accent = data.get("style", {}).get("accent_color", [200, 60, 40])
    bg = data.get("style", {}).get("header_bg", [10, 12, 20])

    for head, body in data.get("sections", []):
        pdf.ln(2)

        # Section headline
        pdf.set_font(font, "B", 12.5)
        pdf.set_text_color(*accent)
        pdf.multi_cell(0, 7, head, new_x="LMARGIN", new_y="NEXT")

        # Accent line
        pdf.set_draw_color(*accent)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(2)

        # Body
        pdf.set_font(font, "", 10)
        pdf.set_text_color(30)
        for para in body.split("\n"):
            para = para.strip()
            if para:
                sanitised = para.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 5.2, sanitised,
                               new_x="LMARGIN", new_y="NEXT")
                pdf.ln(1)

    # Sources section
    sources = data.get("sources", [])
    if sources:
        pdf.ln(4)
        pdf.set_font(font, "B", 11)
        pdf.set_text_color(*accent)
        pdf.cell(0, 7, "Sources", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)

        pdf.set_font(font, "", 8)
        for name, url in sources:
            pdf.set_text_color(0, 60, 160)
            pdf.multi_cell(0, 4.5, f"- {name}", link=url,
                           new_x="LMARGIN", new_y="NEXT")
            pdf.set_text_color(130)
            pdf.multi_cell(0, 4, url, link=url,
                           new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)

    pdf.output(output_path)
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 build_briefing.py config.json output.pdf")
        sys.exit(1)

    config_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(config_path) as f:
        data = json.load(f)

    build_pdf(data, output_path)
    file_size = os.path.getsize(output_path)
    print(f"✅ {output_path} ({file_size:,} bytes)")

    # Verify
    try:
        from pypdf import PdfReader
        r = PdfReader(output_path)
        link_count = sum(1 for p in r.pages
                         for a in (p.get("/Annots") or []))
        print(f"   {len(r.pages)} pages, {link_count} links")
    except ImportError:
        pass
