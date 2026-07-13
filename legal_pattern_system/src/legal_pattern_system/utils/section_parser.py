from __future__ import annotations

import re

from legal_pattern_system.models import Section
from legal_pattern_system.utils.text_cleaning import normalize_heading


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
FIELD_RE = re.compile(r"^\*\*(.+?):\*\*\s*(.+?)\s*$")


def parse_markdown_sections(text: str) -> tuple[str, list[Section]]:
    matches = list(HEADING_RE.finditer(text))
    if not matches:
        return "UNTITLED", []

    title = matches[0].group(2).strip()
    sections: list[Section] = []

    for index, match in enumerate(matches):
        level = len(match.group(1))
        heading = normalize_heading(match.group(2))
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if level == 1:
            continue
        sections.append(Section(heading=heading, level=level, content=content))

    return title, sections


def extract_bold_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        match = FIELD_RE.match(line.strip())
        if match:
            fields[match.group(1).strip()] = match.group(2).strip().rstrip("  ")
    return fields

