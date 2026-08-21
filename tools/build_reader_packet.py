"""Build the printable reader packet — cover note + all six chapters → one PDF.

Made for handing to a real reader on paper. Print-first decisions:

* Background is near-white, not full hemp. A full-bleed tint looks right on
  screen and eats a cartridge on paper; the hemp tone is kept for the cover
  page and the pull-quote rules only.
* Playfair Display / Source Sans 3 are not installed on this box, so the CSS
  names them first and falls back to Georgia / Source Sans-alikes. On a machine
  with the real faces it will pick them up with no change here.
* Each chapter starts on a fresh page, and the three questions go at the FRONT,
  so the reader knows what they are looking for before they start reading.

Usage:  python3 tools/build_reader_packet.py
Output: dist/historys-ledger-reader-packet.pdf
"""
from __future__ import annotations

import html
import subprocess
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "content" / "chapters"
DIST = ROOT / "dist"

# Palette from the 2026-07-26 brand board. Two values were read off a raster
# image and should be re-confirmed against vector source before print.
INK, NAVY, OXBLOOD, BRASS, HEMP, WALNUT = (
    "#1A1A1A", "#1F2F4A", "#8B0F1A", "#B08D3C", "#F3EDE1", "#4B3B27",
)

CSS = f"""
@page {{ size: Letter; margin: 20mm 18mm 18mm; }}
* {{ box-sizing: border-box; }}
body {{
  font-family: "Source Sans 3","Source Sans Pro",Calibri,"Helvetica Neue",sans-serif;
  color: {INK}; font-size: 11.2pt; line-height: 1.62; margin: 0;
  -webkit-print-color-adjust: exact; print-color-adjust: exact;
}}
h1,h2,h3 {{ font-family: "Playfair Display",Georgia,"Times New Roman",serif; color:{NAVY}; }}

/* ── cover ───────────────────────────────────────────────── */
.cover {{
  background:{HEMP}; text-align:center; padding:52mm 16mm 20mm;
  height:100%; page-break-after:always;
}}
.cover img {{ width:30mm; height:30mm; }}
.cover h1 {{ font-size:34pt; margin:8mm 0 2mm; letter-spacing:.5px; }}
.cover .rule {{ width:52mm; height:2px; background:{BRASS}; margin:5mm auto; }}
.cover .tag {{ font-size:12pt; letter-spacing:2.6px; text-transform:uppercase; color:{WALNUT}; }}
.cover .claim {{ font-family:"Playfair Display",Georgia,serif; font-size:15pt; font-style:italic;
                 color:{NAVY}; margin:12mm auto 0; max-width:120mm; }}
.cover .site {{ margin-top:22mm; font-size:10pt; letter-spacing:1.6px; color:{WALNUT}; }}

/* ── the ask ─────────────────────────────────────────────── */
.ask {{ page-break-after:always; padding-top:6mm; }}
.ask h2 {{ font-size:20pt; margin:0 0 4mm; }}
.ask ol {{ padding-left:6mm; }}
.ask li {{ margin-bottom:5mm; }}
.ask .q {{ font-weight:700; color:{NAVY}; }}
.ask .note {{ background:{HEMP}; border-left:3px solid {OXBLOOD};
              padding:5mm 6mm; margin:8mm 0; font-size:10.6pt; }}

/* ── chapters ────────────────────────────────────────────── */
.chapter {{ page-break-before:always; }}
.chapter h1 {{ font-size:23pt; line-height:1.2; margin:0 0 1mm; }}
.chapter h2 {{ font-size:13.5pt; margin:8mm 0 2mm;
               border-bottom:1px solid {BRASS}; padding-bottom:1.5mm; }}
.chapter > p:first-of-type {{ color:{WALNUT}; font-size:10pt;
                              letter-spacing:.6px; margin:0 0 6mm; }}
blockquote {{ margin:5mm 0; padding:3mm 0 3mm 6mm; border-left:3px solid {OXBLOOD};
              font-family:"Playfair Display",Georgia,serif; font-style:italic;
              font-size:12pt; color:{NAVY}; }}
blockquote p {{ margin:0; }}
strong {{ color:{NAVY}; }}
hr {{ border:0; border-top:1px solid {BRASS}; margin:8mm 0 4mm; }}
ul {{ padding-left:6mm; }}
li {{ margin-bottom:1.5mm; }}
code {{ font-family:"IBM Plex Mono",Consolas,monospace; font-size:10pt; }}
"""

ASK = f"""
<div class="ask">
  <h2>Would you read this?</h2>
  <p>Six sample chapters follow — each is a five-to-ten minute read. They are
  drafts. Please be blunt; harsh feedback is the most useful kind.</p>
  <div class="note"><strong>What this is.</strong> A history built on primary
  sources, which tries to hold both the achievement and the cost of the same
  event, and hands the judgment back to the reader rather than making it for
  them.</div>
  <ol>
    <li><span class="q">Did it read as fair, or did it feel like it was pushing
      a side?</span><br>This is the one that matters most. If you lean left, did
      it feel too soft on America? If you lean right, too hard? Either answer is
      useful.</li>
    <li><span class="q">Did anything strike you as factually wrong, or
      missing?</span></li>
    <li><span class="q">Would you use this — for your kids, your classroom, or
      yourself? Would you pay for it?</span></li>
  </ol>
  <p style="margin-top:10mm;color:{WALNUT}">There are no wrong answers, and
  "I wouldn't use it" is a completely acceptable one.</p>
</div>
"""


def main() -> None:
    DIST.mkdir(exist_ok=True)
    md = markdown.Markdown(extensions=["extra", "sane_lists"])

    body = [ASK]
    for path in sorted(CHAPTERS.glob("*.md")):
        md.reset()
        body.append(f'<div class="chapter">{md.convert(path.read_text(encoding="utf-8"))}</div>')

    # The COVER uses the full seal — at 30mm the ring text is legible and is
    # the right register for print. The favicon is the monogram alone; do not
    # swap them.
    mark = (ROOT / "design" / "seal-candidate-2026-07-26.png").resolve().as_uri()
    cover = f"""
    <div class="cover">
      <img src="{mark}" alt="">
      <h1>History&rsquo;s Ledger</h1>
      <div class="rule"></div>
      <div class="tag">Truth on Record</div>
      <div class="claim">&ldquo;The record speaks. You decide.&rdquo;</div>
      <div class="site">HISTORYSLEDGER.COM</div>
    </div>"""

    doc = (f"<!doctype html><html><head><meta charset='utf-8'>"
           f"<title>History's Ledger — reader packet</title><style>{CSS}</style></head>"
           f"<body>{cover}{''.join(body)}</body></html>")

    src = DIST / "reader-packet.html"
    src.write_text(doc, encoding="utf-8")
    out = DIST / "historys-ledger-reader-packet.pdf"

    subprocess.run(
        ["google-chrome", "--headless", "--disable-gpu", "--no-sandbox",
         "--no-pdf-header-footer", f"--print-to-pdf={out}", src.as_uri()],
        check=True, capture_output=True, timeout=180,
    )
    kb = out.stat().st_size // 1024
    print(f"  {out.relative_to(ROOT)}  ({kb} KB)")


if __name__ == "__main__":
    main()
