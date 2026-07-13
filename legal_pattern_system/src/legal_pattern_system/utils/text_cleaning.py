from __future__ import annotations


MOJIBAKE_REPLACEMENTS = {
    "\u00e2\u201a\u00ac": "\u20ac",
    "\u00c2\u00a7": "\u00a7",
    "\u00c3\u0178": "\u00df",
    "\u00c3\u00a4": "\u00e4",
    "\u00c3\u00b6": "\u00f6",
    "\u00c3\u00bc": "\u00fc",
    "\u00c3\u201e": "\u00c4",
    "\u00c3\u2013": "\u00d6",
    "\u00c3\u0153": "\u00dc",
    "\u00c3\u00a9": "\u00e9",
    "\u00e2\u20ac\u0153": '"',
    "\u00e2\u20ac\u009d": '"',
    "\u00e2\u20ac\u2122": "'",
}


def clean_text(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    for broken, fixed in MOJIBAKE_REPLACEMENTS.items():
        cleaned = cleaned.replace(broken, fixed)
    return cleaned


def normalize_heading(heading: str) -> str:
    return " ".join(heading.strip().strip(":").upper().split())

