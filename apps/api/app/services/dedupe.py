from __future__ import annotations

import re
from collections import Counter

from shared.utils.text import normalize_text


_word_re = re.compile(r"[a-z0-9']+")


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return _word_re.findall(normalized)


def token_overlap_ratio(a: str, b: str) -> float:
    tokens_a = tokenize(a)
    tokens_b = tokenize(b)
    if not tokens_a or not tokens_b:
        return 0.0

    counts_a = Counter(tokens_a)
    counts_b = Counter(tokens_b)
    intersection = sum((counts_a & counts_b).values())
    union = sum((counts_a | counts_b).values())
    if union == 0:
        return 0.0
    return intersection / union


def is_similar(a: str, b: str, threshold: float = 0.85) -> bool:
    return token_overlap_ratio(a, b) >= threshold
