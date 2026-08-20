from __future__ import annotations

import math
import re
from collections import Counter

TOKEN_PATTERN = re.compile(r"[a-zA-Z][a-zA-Z_]+")


def tokenize(text: str) -> list[str]:
    """Return deterministic lowercase word tokens used by the local text model."""

    return [token.lower() for token in TOKEN_PATTERN.findall(text)]


class TfidfVectorizer:
    """Build a deterministic TF-IDF matrix without an external machine-learning dependency."""

    def __init__(self) -> None:
        self.idf: dict[str, float] = {}

    def fit(self, documents: list[str]) -> None:
        document_count = len(documents)
        document_frequency: Counter[str] = Counter()
        for document in documents:
            document_frequency.update(set(tokenize(document)))
        self.idf = {
            token: math.log((1 + document_count) / (1 + frequency)) + 1
            for token, frequency in document_frequency.items()
        }

    def transform(self, document: str) -> dict[str, float]:
        term_frequency = Counter(tokenize(document))
        if not term_frequency:
            return {}
        max_count = max(term_frequency.values())
        return {
            token: (count / max_count) * self.idf.get(token, 0.0)
            for token, count in term_frequency.items()
        }


def cosine_similarity(left: dict[str, float], right: dict[str, float]) -> float:
    """Return cosine similarity, using zero for vectors with no magnitude."""

    if not left or not right:
        return 0.0
    shared_tokens = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in shared_tokens)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
