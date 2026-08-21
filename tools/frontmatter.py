"""A frontmatter parser small enough to read in one sitting.

stdlib only, deliberately: this repo has no dependency manifest and adding
PyYAML to parse six scalar fields would be the largest change in the project.
Supports exactly what the source schema uses — scalars, inline [a, b] lists,
and block sequences (`key:` followed by indented `- item` lines, needed for
values like quotations that contain commas).
"""
from __future__ import annotations


def parse(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end = i
            break
    if end is None:
        return {}, text

    fields: dict = {}
    body_lines = lines[1:end]
    i = 0
    while i < len(body_lines):
        line = body_lines[i].strip()
        i += 1
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition(":")
        key, value = key.strip(), value.strip()
        if value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            fields[key] = [v.strip() for v in inner.split(",") if v.strip()]
        elif not value:
            items = []
            while i < len(body_lines) and body_lines[i].lstrip().startswith("- "):
                items.append(body_lines[i].lstrip()[2:].strip())
                i += 1
            fields[key] = items if items else ""
        else:
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value
    return fields, "\n".join(lines[end + 1:])
