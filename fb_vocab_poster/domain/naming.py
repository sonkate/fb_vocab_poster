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


def basename_month(basename: str) -> str:
    """The `YYYY-MM` folder a basename's own timestamp belongs in, e.g.
    `work-email_B1_20260908-231010` -> `2026-09`. Read from the timestamp the
    draft was created with, not the system clock at render time, so rebuilding
    an old draft's video lands back in the same month folder instead of
    wherever `build` happened to run today."""
    timestamp = basename.rsplit("_", 1)[-1]
    created_at = datetime.strptime(timestamp, TIMESTAMP_FORMAT)
    return created_at.strftime("%Y-%m")
