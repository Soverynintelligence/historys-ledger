"""Fetch a source document and write a source record.

The only writer of body text under content/sources/. Text may only exist here
if it came from a URL that returned successfully.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import urllib.error
import urllib.request
from datetime import date

from tools.frontmatter import parse
from tools.source_records import load_all

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCES = os.path.join(HERE, "content", "sources")

ORDER = (
    "id", "title", "author", "date", "type", "repository", "url", "rights",
    "band", "callout", "cited_by", "fetched_at", "sha256",
)


def _looks_like_html(text: str) -> bool:
    head = text.lstrip()[:200].lower()
    return head.startswith("<!doctype") or head.startswith("<html") or "<body" in head


def html_to_text(html: str) -> str:
    """Collapse HTML to plain text so quote matching is not broken by tags."""
    import re

    text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    entities = {
        "&nbsp;": " ",
        "&amp;": "&",
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": '"',
        "&#39;": "'",
        "&apos;": "'",
        "&mdash;": "—",
        "&ndash;": "–",
        "&hellip;": "…",
        "&#8211;": "–",
        "&#8212;": "—",
        "&#8216;": "'",
        "&#8217;": "'",
        "&#8220;": '"',
        "&#8221;": '"',
        "&#8230;": "…",
    }
    for a, b in entities.items():
        text = text.replace(a, b)
    text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)
    text = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), text)
    return re.sub(r"[ \t\r\f\v]+", " ", text).strip()


def fetch(url: str, opener=None) -> tuple[str, str]:
    """Return (text, sha256 hex). opener(url) -> str for tests.

    Network fetches of HTML pages are reduced to plain text before hashing and
    storage so the provenance gate matches chapter quotations against document
    wording rather than markup. Injected openers (tests) are left untouched.
    """
    if opener is not None:
        text = opener(url)
    else:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "HistorysLedger-SourceFetch/1.0"},
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read()
            ctype = (resp.headers.get("Content-Type") or "").lower()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace")
        if "html" in ctype or _looks_like_html(text):
            text = html_to_text(text)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text, digest


def _format_list_field(key: str, val: list) -> list[str]:
    """Inline [a, b] for simple tokens; block sequence when items hold commas."""
    if key == "covers_quotations" or any("," in str(v) for v in val):
        lines = [f"{key}:"]
        for item in val:
            lines.append(f"  - {item}")
        return lines
    return [f"{key}: [{', '.join(val)}]"]


def render_record(fields: dict, text: str) -> str:
    lines = ["---"]
    for key in ORDER:
        val = fields.get(key)
        if val is None or val == "":
            continue
        if isinstance(val, list):
            lines.extend(_format_list_field(key, val))
        else:
            lines.append(f"{key}: {val}")
    # any extra keys
    for key, val in fields.items():
        if key in ORDER or val is None or val == "":
            continue
        if isinstance(val, list):
            lines.extend(_format_list_field(key, val))
        else:
            lines.append(f"{key}: {val}")
    lines.append("---")
    lines.append("")
    if text:
        lines.append(text.rstrip())
        lines.append("")
    return "\n".join(lines)


def reverify(sources_dir: str, opener=None) -> list[str]:
    problems = []
    for record in load_all(sources_dir):
        url = record.get("url")
        if not url:
            continue
        try:
            fetch(url, opener=opener)
        except Exception as exc:
            problems.append(f"{record.get('id', '?')}: {url} — {exc}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Fetch or reverify source records.")
    ap.add_argument("--reverify", action="store_true")
    ap.add_argument("--id")
    ap.add_argument("--url")
    ap.add_argument("--title")
    ap.add_argument("--date")
    ap.add_argument("--type", default="document")
    ap.add_argument("--rights", default="public-domain")
    ap.add_argument("--callout")
    ap.add_argument("--cited-by", dest="cited_by")
    ap.add_argument("--author", default="")
    ap.add_argument("--repository", default="")
    ap.add_argument("--band", default="")
    ap.add_argument("--no-fetch", action="store_true",
                    help="Write metadata only (no body) — for restricted/absent docs")
    args = ap.parse_args(argv)

    if args.reverify:
        problems = reverify(SOURCES)
        for p in problems:
            print(p)
        print(f"{len(problems)} unreachable URL(s)." if problems else "All URLs still fetch.")
        return 1 if problems else 0

    required = ("id", "url", "title", "date", "callout", "cited_by")
    if args.no_fetch:
        required = ("id", "title", "date", "callout", "cited_by")
    missing = [k for k in required if not getattr(args, k.replace("-", "_"), None)]
    # cited_by uses cited_by attr
    if not args.id or not args.title or not args.date or not args.callout or not args.cited_by:
        if not args.reverify:
            print("Need --id --title --date --callout --cited-by"
                  + (" --url" if not args.no_fetch else ""), file=sys.stderr)
            return 2

    fields = {
        "id": args.id,
        "title": args.title,
        "author": args.author,
        "date": args.date,
        "type": args.type,
        "repository": args.repository,
        "rights": args.rights,
        "callout": args.callout,
        "cited_by": [s.strip() for s in args.cited_by.split(",") if s.strip()],
    }
    if args.band:
        fields["band"] = [s.strip() for s in args.band.split(",") if s.strip()]

    text = ""
    if args.no_fetch or args.rights == "restricted":
        fields.pop("url", None)
    else:
        fields["url"] = args.url
        text, digest = fetch(args.url)
        fields["fetched_at"] = date.today().isoformat()
        fields["sha256"] = digest

    os.makedirs(SOURCES, exist_ok=True)
    path = os.path.join(SOURCES, f"{args.id}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_record(fields, text))
    print(f"wrote {path} ({len(text)} chars body)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
