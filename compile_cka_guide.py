#!/usr/bin/env python3
"""Compile CKA_Master_Guide.md to CKA_Master_Guide.pdf via WeasyPrint."""

from pathlib import Path

import markdown
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent
MD = ROOT / "CKA_Master_Guide.md"
PDF = ROOT / "CKA_Master_Guide.pdf"

CSS = """
@page { size: A4; margin: 18mm 16mm; }
body { font-family: DejaVu Sans, sans-serif; font-size: 10pt; line-height: 1.45; color: #1a1a1a; }
h1 { font-size: 22pt; border-bottom: 2px solid #326ce5; padding-bottom: 6px; color: #326ce5; }
h2 { font-size: 16pt; margin-top: 1.2em; color: #1a4480; page-break-after: avoid; }
h3, h4 { page-break-after: avoid; }
code, pre { font-family: DejaVu Sans Mono, monospace; font-size: 8.5pt; }
pre { background: #f4f6f8; border: 1px solid #d0d7de; padding: 8px; white-space: pre-wrap; }
blockquote { border-left: 4px solid #326ce5; margin: 12px 0; padding: 8px 12px; background: #eef4ff; }
table { border-collapse: collapse; width: 100%; margin: 10px 0; font-size: 9pt; }
th, td { border: 1px solid #ccc; padding: 6px 8px; text-align: left; }
th { background: #e8eef7; }
"""


def main() -> None:
    text = MD.read_text(encoding="utf-8")
    body = markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "toc", "sane_lists"],
    )
    html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
    HTML(string=html, base_url=str(ROOT)).write_pdf(PDF)
    print(f"Wrote {PDF} ({PDF.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
