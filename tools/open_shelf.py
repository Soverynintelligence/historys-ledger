"""What Atticus may open — computed from open collections, not remembered.

The homepage chip asks "What shelves are open in this library?" The answer
has to come from the same roots() that generate the corpus. A remembered
list is how 1914 stayed off the shelf after the chapter was written.
"""
from __future__ import annotations

from pathlib import Path

from tools.content_roots import roots

# Planned shelves already named on the public landing. Not invented here.
NAMED_NOT_OPEN = [
    "Modern Wars: Korea, Vietnam",
    "Classical World: Greece, Sparta, Rome",
    "Empires: Persian, British",
]


def _title(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def entries() -> list[dict]:
    """Every chapter Atticus may treat as on the open shelf."""
    out: list[dict] = []
    for r in roots():
        if r.get("status") != "open":
            continue
        ch_dir = Path(r["chapters_dir"])
        allowed = set(r.get("open_entries") or [])
        for path in sorted(ch_dir.glob("*.md")):
            if allowed and path.stem not in allowed:
                continue
            title = _title(path)
            out.append({
                "collection_id": r["id"],
                "collection": r["title"],
                "stem": path.stem,
                "title": title,
                "path": str(path),
            })
    return out


def stems() -> set[str]:
    return {e["stem"] for e in entries()}


def render() -> str:
    """Plain inventory. No historical quotations."""
    lines = [
        "# Open shelf",
        "",
        "This is the inventory of entries Atticus may open. It is not a history chapter.",
        "He answers from these entries and the source records behind them.",
        "He refuses everything else. Silence is the product working.",
        "",
    ]
    current = None
    for e in entries():
        if e["collection"] != current:
            if current is not None:
                lines.append("")
            current = e["collection"]
            lines.append(f"## {current} — open")
        extra = ""
        if e["stem"] == "01-how-europe-walked-in" and "1914" not in e["title"]:
            extra = " (1914)"
        lines.append(f"- {e['stem']} — {e['title']}{extra}")
    lines.append("")
    lines.append("## Named, not open")
    for name in NAMED_NOT_OPEN:
        lines.append(f"- {name}")
    lines.append("")
    return "\n".join(lines)
