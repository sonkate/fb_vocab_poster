"""Naming rules for the artefacts a lesson produces.

Kept in the domain because the draft filename encodes lesson identity — topic,
level and when it was written — and every layer reads that same convention.
"""
import re
import unicodedata
from datetime import datetime

from .level import CEFRLevel

_NON_SLUG = re.compile(r"[^a-z0-9]+")
_DJ_STROKE = str.maketrans({"đ": "d", "Đ": "D"})   # NFD doesn't decompose these
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


def _asciify(text: str) -> str:
    """Transliterates Vietnamese to plain ASCII rather than dropping it: an
    accented topic used to slug down to its consonants alone (`công việc`
    became `c-ng-vi-c`), unreadable and not actually English. Filenames stay
    ASCII regardless of what language the topic itself displays in."""
    text = text.translate(_DJ_STROKE)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", text)


def slugify(topic: str) -> str:
    return _NON_SLUG.sub("-", _asciify(topic).lower()).strip("-") or "lesson"


def draft_basename(topic: str, level: CEFRLevel, created_at: datetime) -> str:
    """e.g. `ordering-coffee_B1_20260101-120000` — the stem shared by the draft
    markdown, its narration mp3 and its rendered mp4."""
    return f"{slugify(topic)}_{level}_{created_at.strftime(TIMESTAMP_FORMAT)}"
