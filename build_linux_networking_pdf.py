#!/usr/bin/env python3
"""
Compile Linux_Networking_SRE_Mastery.md into a formatted PDF.
Uses Markdown -> HTML (with Pygments) -> WeasyPrint.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.tables import TableExtension
from markdown.extensions.toc import TocExtension
from weasyprint import CSS, HTML

WORKSPACE = Path(__file__).resolve().parent
DEFAULT_MD = WORKSPACE / "Linux_Networking_SRE_Mastery.md"
DEFAULT_PDF = WORKSPACE / "Linux_Networking_SRE_Mastery.pdf"

PDF_CSS = """
@page {
  size: A4;
  margin: 18mm 16mm 22mm 16mm;
  @bottom-center {
    content: "Linux & Networking SRE Mastery — Page " counter(page);
    font-size: 9pt;
    color: #555;
  }
}
body {
  font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
  font-size: 10pt;
  line-height: 1.45;
  color: #1a1a1a;
}
h1 {
  font-size: 22pt;
  color: #0b3d91;
  border-bottom: 2px solid #0b3d91;
  padding-bottom: 6px;
  page-break-before: always;
}
h1:first-of-type { page-break-before: avoid; }
h2 {
  font-size: 14pt;
  color: #0b3d91;
  margin-top: 1.2em;
  border-bottom: 1px solid #ccc;
}
h3 { font-size: 11.5pt; color: #333; margin-top: 1em; }
h4 { font-size: 10.5pt; color: #444; }
code, pre {
  font-family: "DejaVu Sans Mono", "Liberation Mono", monospace;
  font-size: 8.5pt;
}
pre {
  background: #f4f6f8;
  border: 1px solid #dde2e8;
  border-left: 3px solid #0b3d91;
  padding: 8px 10px;
  overflow-x: auto;
  page-break-inside: avoid;
}
code { background: #eef1f5; padding: 1px 4px; border-radius: 2px; }
table {
  border-collapse: collapse;
  width: 100%;
  margin: 10px 0;
  font-size: 9pt;
  page-break-inside: avoid;
}
th, td {
  border: 1px solid #bbb;
  padding: 5px 8px;
  text-align: left;
}
th { background: #e8eef7; }
blockquote {
  border-left: 4px solid #c9a227;
  background: #fffbea;
  margin: 10px 0;
  padding: 8px 12px;
  page-break-inside: avoid;
}
.callout {
  border: 1px solid #0b3d91;
  background: #eef4ff;
  padding: 10px;
  margin: 10px 0;
}
hr { border: none; border-top: 1px solid #ccc; margin: 16px 0; }
ul, ol { margin: 6px 0 6px 18px; }
li { margin-bottom: 4px; }
#TOC { page-break-after: always; }
#TOC ul { list-style: none; padding-left: 0; }
#TOC > ul > li { font-weight: bold; margin-top: 6px; }
#TOC ul ul { padding-left: 16px; font-weight: normal; }
a { color: #0b3d91; text-decoration: none; }
"""


def md_to_html(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    html_body = markdown.markdown(
        text,
        extensions=[
            FencedCodeExtension(),
            CodeHiliteExtension(css_class="highlight", guess_lang=False),
            TableExtension(),
            TocExtension(
                toc_depth="2-3",
                anchorlink=True,
                permalink=True,
            ),
        ],
        output_format="html5",
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>Linux &amp; Networking SRE Mastery</title>
</head>
<body>
{html_body}
</body>
</html>"""


def build_pdf(md_path: Path, pdf_path: Path) -> None:
    if not md_path.is_file():
        print(f"ERROR: Markdown source not found: {md_path}", file=sys.stderr)
        sys.exit(1)
    html = md_to_html(md_path)
    HTML(string=html, base_url=str(md_path.parent)).write_pdf(
        str(pdf_path),
        stylesheets=[CSS(string=PDF_CSS)],
    )
    size_kb = pdf_path.stat().st_size // 1024
    print(f"Generated {pdf_path} ({size_kb} KB, {md_path.stat().st_size // 1024} KB source MD)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Linux Networking SRE handbook PDF")
    parser.add_argument("--input", type=Path, default=DEFAULT_MD)
    parser.add_argument("--output", type=Path, default=DEFAULT_PDF)
    args = parser.parse_args()
    build_pdf(args.input.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
