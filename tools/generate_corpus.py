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


def main(argv: list[str] | None = None) -> int:
    from tools.content_roots import roots

    ap = argparse.ArgumentParser()
    ap.add_argument("--chapters", default=CHAPTERS)
    ap.add_argument("--out", default=DEFAULT_OUT)
    args = ap.parse_args(argv)

    # Default: merge every open collection into the Atticus corpus dir.
    if args.chapters == CHAPTERS:
        all_paths: list[str] = []
        for r in roots():
            if r.get("status") != "open":
                continue
            paths = generate(r["chapters_dir"], args.out)
            all_paths.extend(paths)
            print(f"  from {r['id']}: {len(paths)}")
        # Also copy open-collection sources into atticus/source_records when present
        src_out = os.path.join(os.path.dirname(args.out.rstrip("/")), "source_records")
        if os.path.isdir(src_out) or True:
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
        print(f"{len(all_paths)} chapter(s) → {args.out}")
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
