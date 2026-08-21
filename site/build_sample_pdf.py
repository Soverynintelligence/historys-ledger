#!/usr/bin/env python
"""Build sample-chapters.pdf from the Atticus corpus.

    python build_sample_pdf.py

The original PDF was printed from headless Chrome by hand and its source HTML
was never kept, so when a seventh chapter was written on 2026-08-07 the download
silently went stale — the site offered six chapters while the site's own agent
answered from seven. A build nobody can repeat is a build that drifts.

This reads the chapters straight from the corpus that Atticus serves, so the PDF
and the agent cannot disagree about what exists. Chrome is still the renderer,
for visual continuity with the original.

Palette and faces are taken from index.html so the download looks like the site
rather than like a different product.
"""
from __future__ import annotations

import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORPUS = Path.home() / "atticus" / "corpus"
OUT = HERE / "sample-chapters.pdf"

CSS = """
@page { size: A4; margin: 20mm 18mm; }
body { font-family: "EB Garamond", Garamond, Georgia, serif; font-size: 11pt;
       line-height: 1.62; color: #1B1A17; background: #fff; }
.mono { font-family: "IBM Plex Mono", ui-monospace, monospace; }
h1 { font-family: "Playfair Display", Georgia, serif; font-size: 25pt;
     font-weight: 600; color: #1F2F4A; margin: 0 0 1mm 0; line-height: 1.14;
     page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
.chapline { font-family: "IBM Plex Mono", monospace; font-size: 8.5pt;
            letter-spacing: .09em; text-transform: uppercase; color: #4B3B27;
            border-bottom: 1.5px solid #8B0F1A; padding-bottom: 3mm;
            margin-bottom: 6mm; }
h2 { font-family: "Playfair Display", Georgia, serif; font-size: 13.5pt;
     color: #1F2F4A; margin: 8mm 0 2mm; page-break-after: avoid; }
h3 { font-size: 11.5pt; color: #4B3B27; margin: 6mm 0 1.5mm; page-break-after: avoid; }
p { margin: 0 0 3.2mm; }
blockquote { margin: 4mm 0 4mm 4mm; padding-left: 4mm;
             border-left: 2.5px solid #B08D3C; color: #2b2822; font-style: italic; }
blockquote p { margin: 0 0 1.5mm; }
strong { color: #1B1A17; }
table { width: 100%; border-collapse: collapse; margin: 4mm 0; font-size: 9.5pt;
        page-break-inside: avoid; }
th, td { border: 1px solid rgba(75,59,39,.34); padding: 1.8mm 2.4mm;
         text-align: left; vertical-align: top; }
th { background: #EDE3C8; font-family: "IBM Plex Mono", monospace;
     font-size: 8pt; letter-spacing: .05em; text-transform: uppercase; }
hr { border: 0; border-top: 1px solid rgba(75,59,39,.17); margin: 7mm 0; }
code { font-family: "IBM Plex Mono", monospace; font-size: 9.5pt; }
/* The provenance callouts are the point of the product — make them read as
   apparatus rather than as body text. */
.psource { font-family: "IBM Plex Mono", monospace; font-size: 8.6pt;
           letter-spacing: .03em; color: #8B0F1A; background: #EDE3C8;
           border-left: 3px solid #8B0F1A; padding: 2mm 3mm; margin: 3.5mm 0;
           page-break-inside: avoid; }
.cover { text-align: center; padding-top: 55mm; page-break-after: always; }
.cover h1 { page-break-before: avoid; font-size: 40pt; border: 0; }
.cover .sub { font-size: 14pt; font-style: italic; color: #4B3B27; margin-top: 2mm; }
.cover .meta { margin-top: 22mm; font-family: "IBM Plex Mono", monospace;
               font-size: 9pt; letter-spacing: .1em; text-transform: uppercase;
               color: #4B3B27; line-height: 2; }
"""

TITLES = {
    "01": "The Founding", "02": "Slavery & Emancipation", "03": "Reconstruction",
    "04": "Standard Oil", "05": "Civil Rights", "06": "The Cold War",
    "07": "The Bullet and the Podium",
}


def md_to_html(md: str) -> str:
    """Minimal, deliberate Markdown. Not a general converter — it only has to
    handle the shapes the corpus actually uses, and it must never silently drop
    a Primary Source callout, which is the one line that carries the product."""
    out, in_table, in_quote = [], False, False

    def inline(t: str) -> str:
        t = html.escape(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
        t = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", t)
        t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
        t = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1", t)   # print: drop link chrome
        return t

    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set("".join(cells)) <= set("-: "):
                continue
            if not in_table:
                out.append("<table>"); in_table = True
                out.append("<tr>" + "".join(f"<th>{inline(c)}</th>" for c in cells) + "</tr>")
                continue
            out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>"); in_table = False

        if line.startswith(">"):
            if not in_quote:
                out.append("<blockquote>"); in_quote = True
            out.append(f"<p>{inline(line.lstrip('> ').strip())}</p>")
            continue
        if in_quote:
            out.append("</blockquote>"); in_quote = False

        if line.startswith("**Primary Source:**"):
            out.append(f'<div class="psource">{inline(line)}</div>'); continue
        if line.startswith("### "):
            out.append(f"<h3>{inline(line[4:])}</h3>"); continue
        if line.startswith("## "):
            out.append(f"<h2>{inline(line[3:])}</h2>"); continue
        if line.startswith("# "):
            out.append(f"<h1>{inline(line[2:])}</h1>"); continue
        if line.startswith("---"):
            out.append("<hr>"); continue
        if not line.strip():
            continue
        out.append(f"<p>{inline(line)}</p>")

    if in_table: out.append("</table>")
    if in_quote: out.append("</blockquote>")
    return "\n".join(out)


def main() -> int:
    chapters = sorted(CORPUS.glob("*.md"))
    if not chapters:
        print(f"no chapters found in {CORPUS}", file=sys.stderr)
        return 2
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        print("no chrome binary found", file=sys.stderr)
        return 2

    names = ", ".join(TITLES.get(c.name[:2], c.stem) for c in chapters)
    body = [
        '<div class="cover">',
        "<h1>History&rsquo;s Ledger</h1>",
        '<div class="sub">Read the record. Decide for yourself.</div>',
        f'<div class="meta">Sample chapters<br>{len(chapters)} chapters<br>'
        "Powered by SOVERYN</div>",
        "</div>",
    ]
    for c in chapters:
        body.append(md_to_html(c.read_text()))

    doc = (f"<!doctype html><meta charset='utf-8'><title>History's Ledger — sample chapters</title>"
           f"<style>{CSS}</style>{''.join(body)}")

    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "doc.html"
        src.write_text(doc)
        subprocess.run(
            [chrome, "--headless", "--disable-gpu", "--no-sandbox",
             "--no-pdf-header-footer", f"--print-to-pdf={OUT}", src.as_uri()],
            check=True, capture_output=True, timeout=180)

    kb = OUT.stat().st_size // 1024
    print(f"  {OUT.name}: {kb} KB from {len(chapters)} chapters")
    print(f"  {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
