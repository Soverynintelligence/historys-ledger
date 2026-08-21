"""Discover chapter/source roots: legacy US tree + content/collections/*."""
from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
CONTENT = HERE / "content"
COLLECTIONS = CONTENT / "collections"


def roots() -> list[dict]:
    """Each root: id, title, status, chapters_dir, sources_dir."""
    out: list[dict] = []
    legacy_ch = CONTENT / "chapters"
    legacy_src = CONTENT / "sources"
    if legacy_ch.is_dir() and legacy_src.is_dir():
        meta = _read_yaml_lite(CONTENT / "collection.yaml")
        out.append({
            "id": meta.get("id") or "us-america",
            "title": meta.get("title") or "United States",
            "status": meta.get("status") or "open",
            "chapters_dir": str(legacy_ch),
            "sources_dir": str(legacy_src),
            "site_subdir": "",  # /read/
            "blurb": meta.get("blurb") or "",
            "open_entries": meta.get("open_entries") or [],
        })
    if COLLECTIONS.is_dir():
        for d in sorted(COLLECTIONS.iterdir()):
            if not d.is_dir():
                continue
            ch = d / "chapters"
            src = d / "sources"
            if not ch.is_dir() or not src.is_dir():
                continue
            meta = _read_yaml_lite(d / "collection.yaml")
            out.append({
                "id": meta.get("id") or d.name,
                "title": meta.get("title") or d.name,
                "status": meta.get("status") or "scaffolded",
                "chapters_dir": str(ch),
                "sources_dir": str(src),
                "site_subdir": meta.get("id") or d.name,
                "blurb": meta.get("blurb") or "",
                "eras": meta.get("eras") or [],
                "open_entries": meta.get("open_entries") or [],
            })
    return out


def _read_yaml_lite(path: Path) -> dict:
    if not path.is_file():
        return {}
    fields: dict = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            fields[k] = [x.strip() for x in inner.split(",") if x.strip()]
        else:
            fields[k] = v
    return fields


def all_chapter_dirs() -> list[str]:
    return [r["chapters_dir"] for r in roots() if r.get("status") == "open"]


def all_source_dirs() -> list[str]:
    return [r["sources_dir"] for r in roots() if r.get("status") == "open"]
