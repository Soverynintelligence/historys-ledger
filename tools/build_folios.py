"""Generate the public reading app from chapters + source records.

Each entry is one page inside a shared app shell, with the product's spine as
tabs — not a gated wizard:

  Established   achievement / cost from the chapter's own ✅ / ❌ lines
  Sources       block quotations with apparatus (verified / unverified / unsourced)
  Conflicting   honest empty state until entries carry a real conflict block
  Unknown       what we could not check (apparatus gaps)
  Read          full chapter prose
  Weigh         optional scale (never required to open the record)

Nothing here invents prose. Missing ✅/❌ means the Established tab says so.

Usage:  python3 -m tools.build_folios [outdir]
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import json

from tools.apparatus import apparatus, counts
from tools.callouts import callouts_in
from tools.quoted_spans import MIN_QUOTE_CHARS, norm, quoted_spans
from tools.source_cards import build_for_chapter
from tools.source_records import load_all

ROOT = Path(__file__).resolve().parent.parent
CHAPTERS = ROOT / "content" / "chapters"
SOURCES = ROOT / "content" / "sources"
DEFAULT_OUT = Path.home() / "historysledger-site" / "read"

SCALE = [
    ("A", "The achievement outweighs the cost."),
    ("B", "The achievement is greater, but the cost is not incidental to it."),
    ("C", "They cannot be weighed against each other. Both stand."),
    ("D", "The cost is greater, but the principle mattered."),
    ("E", "The cost outweighs the achievement."),
]

STATE_WORD = {
    "verified": "Verified",
    "unverified": "Cited, unchecked",
    "unsourced": "Unverified",
}

_QUOTE = re.compile(r"^> \*[\"“](.+?)[\"”]\*\s*$(?:\n^> — (.+?)$)?", re.M)


def parse_chapter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    title = next((l[2:].strip() for l in lines if l.startswith("# ")), path.stem)
    name, _, subtitle = title.partition(" — ")

    def block(marker: str) -> str:
        for l in lines:
            if l.startswith(marker):
                return l[len(marker) :].strip()
        return ""

    takeaway = ""
    for l in lines:
        if l.startswith("**The takeaway:**"):
            takeaway = l[len("**The takeaway:**") :].strip()
            break

    quotes = [
        {"span": m.group(1).strip(), "attribution": (m.group(2) or "").strip()}
        for m in _QUOTE.finditer(text)
    ]

    return {
        "stem": path.stem,
        "name": name.strip(),
        "subtitle": subtitle.strip(),
        "achieved": block("✅"),
        "cost": block("❌"),
        "takeaway": takeaway,
        "quotes": quotes,
        "text": text,
        "callouts": callouts_in(text),
    }


def _md(s: str) -> str:
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    return s


def _lead(block: str) -> str:
    m = re.match(r"\*\*(.+?)\*\*", block)
    return m.group(1).strip() if m else block.split(".")[0].strip()


def _tap(card_id: str, inner_html: str, *, kind: str = "quote") -> str:
    """A button that opens a source card. inner_html is already escaped/marked."""
    cid = html.escape(card_id, quote=True)
    return (
        f'<button type="button" class="tap tap-{kind}" data-open-card="{cid}" '
        f'aria-haspopup="dialog">'
        f"{inner_html}"
        f'<span class="tap-hint" aria-hidden="true">source</span></button>'
    )


def _linkify_quotes(raw: str, span_to: dict[str, str]) -> str:
    """Wrap long quoted spans that map to a card. Longest-first to avoid nesting."""
    if not span_to:
        return _md(raw)
    # Find occurrences of each span in the raw (unescaped) string
    hits: list[tuple[int, int, str]] = []
    for span_key, card_id in span_to.items():
        # recover a display span from key is lossy; search using apparatus keys
        # by scanning quoted_spans of this fragment
        pass
    # Prefer actual quoted_spans present in this fragment
    for span in sorted(quoted_spans(raw), key=len, reverse=True):
        if len(norm(span)) < MIN_QUOTE_CHARS:
            continue
        key = " ".join(span.split()).lower()
        card_id = span_to.get(key)
        if not card_id:
            continue
        start = raw.find(span)
        if start < 0:
            # try with curly/straight variants already in text
            continue
        hits.append((start, start + len(span), card_id))

    if not hits:
        return _md(raw)

    # resolve overlaps: keep earliest, longest
    hits.sort(key=lambda h: (h[0], -(h[1] - h[0])))
    chosen: list[tuple[int, int, str]] = []
    for h in hits:
        if any(not (h[1] <= c[0] or h[0] >= c[1]) for c in chosen):
            continue
        chosen.append(h)
    chosen.sort(key=lambda h: h[0])

    parts: list[str] = []
    cursor = 0
    for start, end, card_id in chosen:
        if start > cursor:
            parts.append(_md(raw[cursor:start]))
        inner = _md(raw[start:end])
        parts.append(_tap(card_id, inner, kind="quote"))
        cursor = end
    if cursor < len(raw):
        parts.append(_md(raw[cursor:]))
    return "".join(parts)


def chapter_to_html(
    text: str,
    callout_to: dict[str, str] | None = None,
    span_to: dict[str, str] | None = None,
) -> str:
    """Minimal markdown → HTML. Callouts and long quotes are tappable when mapped."""
    callout_to = callout_to or {}
    span_to = span_to or {}
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    if lines and lines[0].startswith("# "):
        i = 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i < len(lines) and lines[i].startswith("**Chapter"):
            i += 1

    buf: list[str] = []

    def flush_p():
        nonlocal buf
        if not buf:
            return
        para = " ".join(buf).strip()
        buf = []
        if not para:
            return
        if para.startswith("**Primary Source:**"):
            label = para[len("**Primary Source:**") :].strip().rstrip(".")
            # strip markdown emphasis markers for lookup; records store markdown
            card_id = callout_to.get(label) or callout_to.get(
                para[len("**Primary Source:**") :].strip().rstrip(".")
            )
            # try raw callout forms from callouts_in
            for c_label, cid in callout_to.items():
                if c_label.rstrip(".") == label or label in c_label:
                    card_id = cid
                    break
            inner = _md(para)
            if card_id:
                out.append(
                    f'<p class="primary-source">{_tap(card_id, inner, kind="callout")}</p>'
                )
            else:
                out.append(f'<p class="primary-source">{inner}</p>')
        else:
            out.append(f"<p>{_linkify_quotes(para, span_to)}</p>")

    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            flush_p()
            out.append(f"<h2>{_md(line[3:].strip())}</h2>")
        elif line.startswith("---"):
            flush_p()
            out.append("<hr>")
        elif line.startswith("> "):
            flush_p()
            chunk = [line[2:]]
            i += 1
            while i < len(lines) and lines[i].startswith("> "):
                chunk.append(lines[i][2:])
                i += 1
            joined = "\n".join(chunk)
            # block quotation line: *"..."*
            m = re.match(r'^\*[\"“](.+?)[\"”]\*\s*$', chunk[0].strip())
            card_id = None
            if m:
                key = " ".join(m.group(1).split()).lower()
                card_id = span_to.get(key)
            body = "<br>".join(
                _linkify_quotes(c, span_to) if not card_id else _md(c) for c in chunk
            )
            if card_id:
                out.append(
                    f"<blockquote><p>{_tap(card_id, body, kind='quote')}</p></blockquote>"
                )
            else:
                out.append(f"<blockquote><p>{body}</p></blockquote>")
            continue
        elif line.startswith("- "):
            flush_p()
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(
                    f"<li>{_linkify_quotes(lines[i][2:].strip(), span_to)}</li>"
                )
                i += 1
            out.append("<ul>" + "".join(items) + "</ul>")
            continue
        elif not line.strip():
            flush_p()
        else:
            buf.append(line.strip())
        i += 1
    flush_p()
    return "\n".join(out)


def shell_head(title: str, description: str, *, depth: str = "../") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<link rel="icon" type="image/png" href="{depth}favicon.png" sizes="32x32">
<link rel="apple-touch-icon" href="{depth}apple-touch-icon.png" sizes="180x180">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,500;0,700;1,400;1,500&family=EB+Garamond:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{depth}app.css">
</head>
<body>
<div class="app-shell">
"""


def shell_bar(active: str, *, depth: str = "../") -> str:
    def link(href: str, label: str, key: str) -> str:
        cur = ' aria-current="page"' if active == key else ""
        return f'<a href="{depth}{href}"{cur}>{label}</a>'

    mark = f"{depth}brand/hl-seal-red-256.png?v=20260814paper"
    return f"""  <header class="app-bar">
    <div class="app-bar-inner">
      <a class="brand" href="{depth}">
        <img src="{mark}" width="32" height="32" alt="" class="brand-mark">
        <span class="brand-text"><b>History&rsquo;s Ledger</b><i>Truth on record</i></span>
      </a>
      <nav class="app-nav" aria-label="Primary">
        {link("read/", "Entries", "entries")}
        <a href="#ask" data-open-atticus>Ask Atticus</a>
      </nav>
    </div>
  </header>
"""


def shell_foot(*, depth: str = "../") -> str:
    return f"""  <footer class="app-footer">
    <span>Truth on record &middot; Provenance matters &middot; Context clarifies</span>
    <span>Powered by <a href="https://soverynintelligence.com">Soveryn</a></span>
  </footer>
</div>
<script src="{depth}app.js"></script>
</body>
</html>
"""


def quote_cards(ch: dict, entries: list[dict], span_to: dict[str, str]) -> str:
    by_span = {}
    for e in entries:
        by_span.setdefault(" ".join(e["span"].split()).lower(), e)

    cards = []
    for q in ch["quotes"]:
        key = " ".join(q["span"].split()).lower()
        e = by_span.get(key)
        state = e["status"] if e else "unsourced"
        card_id = span_to.get(key, "")
        attrib = q["attribution"] or (
            e.get("source_title") if e and e.get("source_title") else ""
        )
        open_attr = (
            f' role="button" tabindex="0" data-open-card="{html.escape(card_id, quote=True)}"'
            if card_id
            else ""
        )
        bits = [f'<blockquote>&ldquo;{_md(q["span"])}&rdquo;</blockquote>']
        if attrib:
            bits.append(f'<span class="src">{_md(attrib)}</span>')

        mark = f'<span class="prov {state}">{STATE_WORD[state]}</span>'
        if e and state == "verified":
            p = e["passages"][0]
            title = e.get("source_title") or ""
            said = title and title.split(",")[0].lower() in attrib.lower()
            bits.append(
                f'{mark}<span class="provwhere">'
                f'{"checked against the document" if said else "in " + html.escape(title)}</span>'
                f'<details class="ctx"><summary>See it where it is written</summary>'
                f'<p>&hellip;{html.escape(p["before"][-260:])} '
                f'<b>{html.escape(p["quoted"])}</b> '
                f'{html.escape(p["after"][:260])}&hellip;</p>'
                + (
                    f'<p class="lnk"><a href="{html.escape(e["url"])}" rel="noopener">'
                    f"Go to the document</a></p>"
                    if e.get("url")
                    else ""
                )
                + "</details>"
            )
        else:
            reason = (e or {}).get(
                "reason", "we could not locate this in any source we hold"
            )
            bits.append(
                f'{mark}<span class="provwhere">{html.escape(reason)}</span>'
            )
        if card_id:
            bits.append(
                f'<p class="card-open"><button type="button" class="btn quiet" '
                f'data-open-card="{html.escape(card_id, quote=True)}">Open source card →</button></p>'
            )
        cards.append(f'<div class="card"{open_attr}>{"".join(bits)}</div>')

    seen = {" ".join(q["span"].split()).lower() for q in ch["quotes"]}
    for e in entries:
        key = " ".join(e["span"].split()).lower()
        if key in seen:
            continue
        state = e["status"]
        card_id = span_to.get(key, e.get("source_id") or "")
        bits = [
            f'<blockquote>&ldquo;{_md(e["span"])}&rdquo;</blockquote>',
            f'<span class="prov {state}">{STATE_WORD[state]}</span>',
        ]
        if state == "verified" and e.get("passages"):
            p = e["passages"][0]
            title = e.get("source_title") or ""
            bits.append(
                f'<span class="provwhere">in {html.escape(title)}</span>'
                f'<details class="ctx"><summary>See it where it is written</summary>'
                f'<p>&hellip;{html.escape(p["before"][-260:])} '
                f'<b>{html.escape(p["quoted"])}</b> '
                f'{html.escape(p["after"][:260])}&hellip;</p></details>'
            )
        else:
            bits.append(
                f'<span class="provwhere">{html.escape(e.get("reason", ""))}</span>'
            )
        if card_id:
            bits.append(
                f'<p class="card-open"><button type="button" class="btn quiet" '
                f'data-open-card="{html.escape(card_id, quote=True)}">Open source card →</button></p>'
            )
        cards.append(f'<div class="card">{"".join(bits)}</div>')

    return "".join(cards) or (
        '<div class="empty-state">This entry has no long quotations marked in '
        "the prose. Primary-source callouts still appear in the Read panel — tap one.</div>"
    )


def callout_list(ch: dict, callout_to: dict[str, str]) -> str:
    if not ch["callouts"]:
        return ""
    items = []
    for c in ch["callouts"]:
        cid = callout_to.get(c, "")
        if cid:
            items.append(
                f'<li><button type="button" class="tap tap-callout" '
                f'data-open-card="{html.escape(cid, quote=True)}">{_md(c)}'
                f'<span class="tap-hint" aria-hidden="true">source</span></button></li>'
            )
        else:
            items.append(f"<li>{_md(c)}</li>")
    return (
        f'<h3 class="mono" style="margin:1.2rem 0 .5rem">Primary sources named in this entry'
        f" <span class=\"note\">— tap to open</span></h3>"
        f"<ul>{''.join(items)}</ul>"
    )


def source_drawer_html() -> str:
    return """
  <div class="card-drawer" id="source-drawer" hidden>
    <div class="card-drawer-backdrop" data-close-card tabindex="-1"></div>
    <aside class="card-drawer-panel" role="dialog" aria-modal="true" aria-labelledby="card-title" tabindex="-1">
      <div class="card-drawer-head">
        <span class="mono" id="card-kicker">Source card</span>
        <button type="button" class="card-close" data-close-card aria-label="Close">&times;</button>
      </div>
      <div class="card-drawer-body">
        <h2 id="card-title"></h2>
        <p class="card-meta mono" id="card-meta"></p>
        <p class="card-status" id="card-status"></p>
        <p class="card-callout" id="card-callout"></p>
        <div id="card-passage" class="card-passage" hidden></div>
        <p class="card-reason" id="card-reason" hidden></p>
        <p class="card-actions" id="card-actions"></p>
      </div>
    </aside>
  </div>
"""


def scale_opts(prefix: str) -> str:
    return "".join(
        f'<button class="opt" type="button" aria-pressed="false" data-i="{i}">'
        f'<span class="k">{k}</span><span>{html.escape(v)}</span></button>'
        for i, (k, v) in enumerate(SCALE)
    )


def render(
    ch: dict,
    entries: list[dict],
    nav: str,
    *,
    cards: dict[str, dict] | None = None,
    callout_to: dict[str, str] | None = None,
    span_to: dict[str, str] | None = None,
) -> str:
    c = counts(entries)
    total = sum(c.values()) or 0
    have_scale = bool(ch["achieved"] and ch["cost"])
    callout_to = callout_to or {}
    span_to = span_to or {}
    cards = cards or {}
    prose = chapter_to_html(ch["text"], callout_to, span_to)

    established = (
        f"""
      <div class="two">
        <div class="col-card gain"><h3>What was achieved</h3><p>{_md(ch["achieved"])}</p></div>
        <div class="col-card cost"><h3>What it cost</h3><p>{_md(ch["cost"])}</p></div>
      </div>
      <p class="note">Both columns are drawn from the same documents. Neither is our characterisation.</p>
"""
        if have_scale
        else """
      <div class="empty-state">This entry does not resolve into a clean achievement/cost
      pair, and is not forced into that shape. Use Read for the full record.</div>
"""
    )

    open_items = [e for e in entries if e["status"] != "verified"]
    unknown_rows = (
        "".join(
            f'<li><span class="prov {e["status"]}">{STATE_WORD[e["status"]]}</span> '
            f'&ldquo;{html.escape(e["span"][:150])}&rdquo; &mdash; '
            f'{html.escape(e.get("reason", ""))}</li>'
            for e in open_items
        )
        or "<li>Every long quotation in this entry was located in a document we hold.</li>"
    )

    weigh = ""
    if have_scale:
        weigh = f"""
    <div class="panel" id="panel-weigh" role="tabpanel" aria-labelledby="tab-weigh">
      <div class="panel-mark"><span class="numeral">VI</span><span class="mono">Optional</span></div>
      <h2>Weigh it — only if you want to.</h2>
      <p class="sub">Nothing here is scored. You can read the whole entry without touching this.</p>
      <fieldset class="scale">
        <legend>Before / first position</legend>
        <p class="sub" style="margin-top:.6rem"><strong>{_md(_lead(ch["achieved"]))}</strong>
        &nbsp;·&nbsp; <strong>{_md(_lead(ch["cost"]))}</strong></p>
        <div class="opts" id="opts0">{scale_opts("0")}</div>
        <p class="note" id="hint0">Choose a starting place, then read. Come back and choose again.</p>
      </fieldset>
      <fieldset class="scale" style="margin-top:1rem">
        <legend>After reading</legend>
        <div class="opts" id="opts1">{scale_opts("1")}</div>
      </fieldset>
      <div class="readout" id="readout" hidden>
        <div class="bar"><span class="tag">Before</span><div class="track"><div class="pip was" id="pipA"></div></div></div>
        <div class="bar"><span class="tag">After</span><div class="track"><div class="pip" id="pipB"></div></div></div>
        <p class="moved" id="moved"></p>
        <p class="note">There is no correct answer. The ledger counts both sides; the weighing is yours.</p>
      </div>
      {f'<div class="takeaway"><h3>The takeaway</h3><p>{_md(ch["takeaway"])}</p></div>' if ch["takeaway"] else ""}
    </div>
"""
    else:
        weigh = f"""
    <div class="panel" id="panel-weigh" role="tabpanel" aria-labelledby="tab-weigh">
      <div class="panel-mark"><span class="numeral">VI</span><span class="mono">Optional</span></div>
      <h2>The takeaway</h2>
      {f'<div class="takeaway"><p>{_md(ch["takeaway"])}</p></div>' if ch["takeaway"] else '<div class="empty-state">No separate takeaway line in this entry.</div>'}
    </div>
"""

    unverified_bit = (
        f'<span class="prov unverified">{c["unverified"]} cited, unchecked</span>'
        if c["unverified"]
        else ""
    )
    unsourced_bit = (
        f'<span class="prov unsourced">{c["unsourced"]} unverified</span>'
        if c["unsourced"]
        else ""
    )
    tally = (
        f'<p class="tallyline">'
        f'<span class="prov verified">{c["verified"]} verified</span>'
        f"{unverified_bit}{unsourced_bit}"
        f'<span class="of"> of {total} long quotations</span></p>'
    )

    body = f"""  <main class="app-main">
    <article class="app-leaf narrow" data-entry="{html.escape(ch["stem"])}">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:1rem;padding-top:1.1rem">
        <p class="mono" style="margin:0">Ledger entry</p>
        <img src="../brand/hl-seal-red-cut.png?v=20260814paper" width="84" height="84" alt="History's Ledger" class="entry-seal"
             srcset="../brand/hl-seal-red-256.png?v=20260814paper 256w, ../brand/hl-seal-red-cut.png?v=20260814paper 900w"
             sizes="84px">
      </div>
      <h1>{_md(ch["name"])} <em>{_md(ch["subtitle"])}</em></h1>
      <p class="sub">Open any tab. In Read, tap a primary source or a long quotation to open its card. Atticus floats bottom-right — ask him anything on the record.</p>
      {tally}
      <div class="progress-rail" data-progress-rail aria-hidden="true">
        <span></span><span></span><span></span><span></span><span></span><span></span>
      </div>

      <div class="challenge-bar">
        <h3>Don&rsquo;t just scroll — interrogate it</h3>
        <p>History is boring when it lectures. Ask Atticus to stress-test this entry, or open the Sources tab and pull a document.</p>
        <div class="chips-row">
          <button type="button" class="atticus-chip" data-ask-atticus="What does this entry claim, in one sentence — from the documents?">One-sentence claim</button>
          <button type="button" class="atticus-chip" data-ask-atticus="Where is the biggest gap in the sources for this entry?">Biggest gap</button>
          <button type="button" class="atticus-chip" data-ask-atticus="Show me one verified quotation and where it sits in the record.">Show a verified quote</button>
          <button type="button" class="btn quiet" data-open-atticus>Ask Atticus →</button>
        </div>
      </div>

      <div class="entry-tabs" role="tablist" aria-label="Entry sections">
        <button class="tab" role="tab" id="tab-established" aria-controls="panel-established" aria-selected="true"><span class="n">I</span>Established</button>
        <button class="tab" role="tab" id="tab-sources" aria-controls="panel-sources" aria-selected="false" tabindex="-1"><span class="n">II</span>Sources</button>
        <button class="tab" role="tab" id="tab-conflict" aria-controls="panel-conflict" aria-selected="false" tabindex="-1"><span class="n">III</span>Conflicting</button>
        <button class="tab" role="tab" id="tab-unknown" aria-controls="panel-unknown" aria-selected="false" tabindex="-1"><span class="n">IV</span>Unknown</button>
        <button class="tab" role="tab" id="tab-read" aria-controls="panel-read" aria-selected="false" tabindex="-1"><span class="n">V</span>Read</button>
        <button class="tab" role="tab" id="tab-weigh" aria-controls="panel-weigh" aria-selected="false" tabindex="-1"><span class="n">VI</span>Weigh</button>
      </div>

      <div class="panel is-active" id="panel-established" role="tabpanel" aria-labelledby="tab-established">
        <div class="panel-mark"><span class="numeral">I</span><span class="mono">Established facts</span></div>
        <h2>What the evidence strongly supports.</h2>
        {established}
      </div>

      <div class="panel" id="panel-sources" role="tabpanel" aria-labelledby="tab-sources">
        <div class="panel-mark"><span class="numeral">II</span><span class="mono">Primary sources</span></div>
        <h2>The words, laws and letters from the time.</h2>
        <p class="sub">Every long quotation carries where it came from. Open a verified one to see the passage it sits in — or open the source card.</p>
        {quote_cards(ch, entries, span_to)}
        {callout_list(ch, callout_to)}
      </div>

      <div class="panel" id="panel-conflict" role="tabpanel" aria-labelledby="tab-conflict">
        <div class="panel-mark"><span class="numeral">III</span><span class="mono">Conflicting accounts</span></div>
        <h2>Where the record disagrees.</h2>
        <div class="empty-state">This entry does not stage a separate conflict dossier. The tension is held in
        Established facts (achievement and cost side by side) and in the sources themselves.
        When two documents disagree by name, that pair will appear here.</div>
      </div>

      <div class="panel" id="panel-unknown" role="tabpanel" aria-labelledby="tab-unknown">
        <div class="panel-mark"><span class="numeral">IV</span><span class="mono">What remains unknown</span></div>
        <h2>What we could not check.</h2>
        <p class="sub">Of {total} long quotations in this entry, {c["verified"]} were located in a document we hold.
        The rest are listed here rather than left to look the same as the ones we could check.</p>
        <ul class="unknown">{unknown_rows}</ul>
        <p class="note">Where the record stops, we stop. &ldquo;Complete&rdquo; is not a status we use.</p>
      </div>

      <div class="panel" id="panel-read" role="tabpanel" aria-labelledby="tab-read">
        <div class="panel-mark"><span class="numeral">V</span><span class="mono">The entry</span></div>
        <h2>Read the full record.</h2>
        <p class="sub">Underlined sources and quotations open a card — held text, restricted, or not held yet.</p>
        <div class="prose">
{prose}
        </div>
      </div>
{weigh}

      <script type="application/json" id="source-cards-data">{json.dumps(cards, ensure_ascii=False)}</script>
{source_drawer_html()}

      <div class="atticus-rail" id="ask-atticus">
        <div class="at-head">
          <strong>Atticus is on every page</strong>
          <span class="mono">Floating · bottom-right</span>
        </div>
        <p class="at-body">The curator button follows you. He answers only from this ledger and the sources behind it —
          and stops when he can&rsquo;t cite.
          <button type="button" class="btn quiet" data-open-atticus style="margin-left:.35rem">Open Atticus →</button></p>
      </div>

      <div class="row" style="margin-top:1.4rem">
        <a class="btn quiet" href="./">All entries</a>
        {nav}
      </div>
    </article>
  </main>
"""

    return (
        shell_head(
            f"History's Ledger — {ch['name']}",
            f"{ch['name']} — established facts, primary sources, and what remains unchecked.",
        )
        + shell_bar("entries")
        + body
        + shell_foot()
    )


def index_page(chapters: list[dict], by_chapter: dict) -> str:
    rows = []
    for ch in chapters:
        c = counts(by_chapter.get(ch["stem"], []))
        total = sum(c.values())
        rows.append(
            f"""
    <a class="entry-link" href="{ch['stem']}.html">
      <h2>{_md(ch['name'])}</h2>
      <p class="sub" style="margin:0 0 .35rem">{_md(ch['subtitle'])}</p>
      <p class="tallyline">
        <span class="prov verified">{c['verified']} verified</span>
        {f'<span class="prov unverified">{c["unverified"]} cited, unchecked</span>' if c['unverified'] else ''}
        {f'<span class="prov unsourced">{c["unsourced"]} unverified</span>' if c['unsourced'] else ''}
        <span class="of">of {total} quotations</span>
      </p>
    </a>"""
        )

    grand = counts([e for v in by_chapter.values() for e in v])
    total = sum(grand.values())
    body = f"""  <main class="app-main">
    <div class="app-leaf narrow">
      <p class="mono" style="padding-top:1.2rem">The entries</p>
      <h1>Read the record.</h1>
      <p class="sub">Each entry states what is established, shows the documents,
      says what it could not check, and hands the judgement back to you.
      Across all {len(chapters)} entries there are {total} long quotations:
      <strong>{grand['verified']}</strong> located in documents we hold,
      <strong>{grand['unverified']}</strong> cited from sources we may not reproduce,
      and <strong>{grand['unsourced']}</strong> we could not verify. That last number
      is printed here for the same reason it is printed everywhere else.</p>
      {''.join(rows)}
      <div class="atticus-rail" id="ask-atticus" style="margin-top:1.6rem">
        <div class="at-head"><strong>Atticus floats on every page</strong><span class="mono">Bottom-right</span></div>
        <p class="at-body">
          <button type="button" class="btn quiet" data-open-atticus>Open Atticus →</button>
          <button type="button" class="atticus-chip" data-ask-atticus="Try to invent a founding date that isn't in the record." style="margin-left:.4rem">Challenge him</button>
        </p>
      </div>
    </div>
  </main>
"""
    return (
        shell_head(
            "History's Ledger — the entries",
            "Primary-source history entries. Every long quotation is marked verified, cited-unchecked, or unverified.",
        )
        + shell_bar("entries")
        + body
        + shell_foot()
    )


def _build_collection(
    out: Path,
    chapters_dir: Path,
    sources_dir: Path,
    *,
    collection_title: str | None = None,
    depth: str = "../",
) -> tuple[list[dict], dict]:
    records = load_all(str(sources_dir)) if sources_dir.is_dir() else []
    entries = apparatus(str(chapters_dir), str(sources_dir))
    by_chapter: dict[str, list[dict]] = {}
    for e in entries:
        by_chapter.setdefault(e["chapter"], []).append(e)

    paths = sorted(chapters_dir.glob("*.md"))
    chapters = [parse_chapter(p) for p in paths]
    out.mkdir(parents=True, exist_ok=True)

    for i, ch in enumerate(chapters):
        nxt = chapters[i + 1] if i + 1 < len(chapters) else None
        nav = (
            f'<a class="btn" href="{nxt["stem"]}.html">Next: {html.escape(nxt["name"])} →</a>'
            if nxt
            else ""
        )
        ch_entries = by_chapter.get(ch["stem"], [])
        cards, callout_to, span_to = build_for_chapter(
            records, ch["stem"], ch_entries
        )
        page = render(
            ch,
            ch_entries,
            nav,
            cards=cards,
            callout_to=callout_to,
            span_to=span_to,
        )
        # Fix relative brand/script depth for nested collections
        if depth != "../":
            page = page.replace('href="../', f'href="{depth}')
            page = page.replace('src="../', f'src="{depth}')
            page = page.replace('href="./"', f'href="./"')
        (out / f"{ch['stem']}.html").write_text(page, encoding="utf-8")
        c = counts(ch_entries)
        print(
            f"  {out.name + '/' if out.name != 'read' else ''}{ch['stem']}.html  "
            f"quotes={len(ch['quotes'])}  "
            f"apparatus {c['verified']}/{sum(c.values())} verified  "
            f"cards={len(cards)}"
        )

    idx = index_page(chapters, by_chapter)
    if collection_title:
        idx = idx.replace(
            "The entries",
            html.escape(collection_title) + " — entries",
            1,
        )
    if depth != "../":
        idx = idx.replace('href="../', f'href="{depth}')
        idx = idx.replace('src="../', f'src="{depth}')
    (out / "index.html").write_text(idx, encoding="utf-8")
    print(f"  {out}/index.html  ({len(chapters)} entries)")
    return chapters, by_chapter


def main(argv=None) -> int:
    from tools.content_roots import roots

    out = Path((argv or sys.argv[1:] or [str(DEFAULT_OUT)])[0])
    out.mkdir(parents=True, exist_ok=True)

    # Legacy US tree at /read/
    _build_collection(out, CHAPTERS, SOURCES)

    # Additional open collections under /read/{id}/
    for r in roots():
        if r["id"] == "us-america" or r.get("status") != "open":
            continue
        sub = r.get("site_subdir") or r["id"]
        dest = out / sub
        depth = "../../"
        print(f"-- collection {r['id']} → {dest}")
        _build_collection(
            dest,
            Path(r["chapters_dir"]),
            Path(r["sources_dir"]),
            collection_title=r.get("title"),
            depth=depth,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
