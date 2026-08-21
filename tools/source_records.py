"""Source records — the documents, as data.

Every rule here exists to keep one promise: a document in this repo was
retrieved from somewhere and can be checked, or it is not here at all. The
schema permits absence everywhere and invention nowhere.
"""
from __future__ import annotations

import os

from tools.frontmatter import parse

REQUIRED = ("id", "title", "date", "type", "rights", "callout", "cited_by")
TYPES = ("document", "artifact", "record-set")
RIGHTS = ("public-domain", "us-government", "restricted")


def load_all(sources_dir: str) -> list[dict]:
    records = []
    for name in sorted(os.listdir(sources_dir)):
        if not name.endswith(".md") or name == "README.md":
            continue
        path = os.path.join(sources_dir, name)
        with open(path, encoding="utf-8") as f:
            fields, body = parse(f.read())
        record = {k: v for k, v in fields.items() if v != ""}
        record["path"] = path
        record["text"] = body.strip()
        records.append(record)
    return records


def validate(record: dict) -> list[str]:
    errors = []
    for field in REQUIRED:
        if not record.get(field):
            errors.append(
                f"{record.get('path', '?')}: missing required field '{field}'"
            )

    stem = os.path.basename(record.get("path", "")).removesuffix(".md")
    if stem and record.get("id") and record["id"] != stem:
        errors.append(
            f"{record['path']}: id '{record['id']}' does not match filename '{stem}'"
        )

    if record.get("type") and record["type"] not in TYPES:
        errors.append(
            f"{record['path']}: type '{record['type']}' not one of {TYPES}"
        )
    if record.get("rights") and record["rights"] not in RIGHTS:
        errors.append(
            f"{record['path']}: rights '{record['rights']}' not one of {RIGHTS}"
        )

    has_text = bool(record.get("text"))
    if has_text and not record.get("url"):
        errors.append(
            f"{record.get('path', '?')}: has text without a url — source text must be "
            "fetched and attributed, never written from memory"
        )
    if has_text and record.get("rights") == "restricted":
        errors.append(
            f"{record['path']}: rights are restricted, so this record must carry no text"
        )
    return errors
