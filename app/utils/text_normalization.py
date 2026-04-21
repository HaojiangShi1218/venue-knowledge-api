from __future__ import annotations

import re

_WHITESPACE_RE = re.compile(r"\s+")
_PUNCTUATION_RE = re.compile(r"[^\w\s-]")

_DASH_TRANSLATION = str.maketrans(
    {
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
        "\u2015": "-",
        "\u2212": "-",
    }
)


def normalize_text(text: str) -> str:
    normalized = text.lower().translate(_DASH_TRANSLATION)
    normalized = normalized.strip()
    normalized = _PUNCTUATION_RE.sub(" ", normalized)
    normalized = normalized.replace("-", " ")
    normalized = _WHITESPACE_RE.sub(" ", normalized)
    return normalized.strip()
