from __future__ import annotations

import re

_whitespace = re.compile(r"\s+")


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    text = text.strip().lower()
    text = _whitespace.sub(" ", text)
    return text
