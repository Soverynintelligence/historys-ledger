"""Generate ~/atticus/corpus from canonical chapters.

Replaces hand-copy-and-scp that stranded chapter 7 outside the canonical repo.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTERS = os.path.join(HERE, "content", "chapters")
CORPUS = os.path.expanduser("~/atticus/corpus")
DEFAULT_OUT = CORPUS


def _names(dirpath: str) -> list[str]:
    if not os.path.isdir(dirpath):
        return []
    return sorted(n for n in os.listdir(dirpath) if n.endswith(".md"))


def generate(chapters_dir: str, out_dir: str) -> list[str]:
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for name in _names(chapters_dir):
        src = os.path.join(chapters_dir, name)
        dst = os.path.join(out_dir, name)
        shutil.copy2(src, dst)
        written.append(dst)
    return written


def generate_open(out_dir: str) -> list[str]:
    """Copy every open-shelf chapter, then write the shelf inventory."""
    from tools.open_shelf import entries, render, stems

    os.makedirs(out_dir, exist_ok=True)
    written: list[str] = []
    allowed = stems()
    for e in entries():
        if e["stem"] not in allowed:
            continue
        dst = os.path.join(out_dir, e["stem"] + ".md")
        shutil.copy2(e["path"], dst)
        written.append(dst)
    shelf = os.path.join(out_dir, "OPEN-SHELF.md")
    with open(shelf, "w", encoding="utf-8") as f:
        f.write(render())
    written.append(shelf)
    return written


def stale(chapters_dir: str, out_dir: str) -> list[str]:
    """Chapter basenames that are missing from out_dir or differ in content."""
    out = []
    for name in _names(chapters_dir):
        target = os.path.join(out_dir, name)
        if not os.path.exists(target):
            out.append(name)
            continue
        with open(os.path.join(chapters_dir, name), encoding="utf-8") as a, open(
            target, encoding="utf-8"
        ) as b:
            if a.read() != b.read():
                out.append(name)
    return out


def stale_open(out_dir: str) -> list[str]:
    """Open-shelf chapter basenames missing from out_dir or drifted."""
    from tools.open_shelf import entries, render

    out: list[str] = []
    for e in entries():
        name = e["stem"] + ".md"
        target = os.path.join(out_dir, name)
        if not os.path.exists(target):
            out.append(name)
            continue
        with open(e["path"], encoding="utf-8") as a, open(target, encoding="utf-8") as b:
            if a.read() != b.read():
                out.append(name)
    shelf = os.path.join(out_dir, "OPEN-SHELF.md")
    if not os.path.exists(shelf) or open(shelf, encoding="utf-8").read() != render():
        out.append("OPEN-SHELF.md")
    return out


def main(argv: list[str] | None = None) -> int:
    from tools.content_roots import roots

    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", default=CHAPTERS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    # Default: merge every open-shelf chapter into the Atticus corpus dir.
    if args.chapters == CHAPTERS:
        all_paths = generate_open(args.out)
        from tools.open_shelf import entries

        by_col: dict[str, int] = {}
        for e in entries():
            by_col[e["collection_id"]] = by_col.get(e["collection_id"], 0) + 1
        for cid, n in by_col.items():
            print(f"  from {cid}: {n}")
        # Also copy open-collection sources into atticus/source_records when present
        src_out = os.path.join(os.path.dirname(args.out.rstrip("/")), "source_records")
        os.makedirs(src_out, exist_ok=True)
        for r in roots():
            if r.get("status") != "open":
                continue
            sdir = r["sources_dir"]
            if not os.path.isdir(sdir):
                continue
            for name in os.listdir(sdir):
                if not name.endswith(".md") or name == "README.md":
                    continue
                shutil.copy2(os.path.join(sdir, name), os.path.join(src_out, name))
        print(f"{len(all_paths)} file(s) → {args.out}")
        return 0

    drift = stale(args.chapters, args.out)
    paths = generate(args.chapters, args.out)
    for p in paths:
        print(p)
    print(f"{len(paths)} chapter(s) → {args.out}")
    if drift:
        print("was stale: " + ", ".join(drift))
        print("\nThe Spark serves its own copy. Push it:")
        print(f"  scp {args.out}/*.md soverynspark@10.10.10.2:~/atticus/corpus/")
        print("  ssh soverynspark@10.10.10.2 'systemctl --user restart atticus'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
