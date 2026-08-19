"""Naming rules for the artefacts a lesson produces.

Kept in the domain because the draft filename encodes lesson identity — topic,
level and when it was written — and every layer reads that same convention.
"""
import re
from datetime import datetime

from .level import CEFRLevel

_NON_SLUG = re.compile(r"[^a-z0-9]+")
TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S"


def slugify(topic: str) -> str:
    return _NON_SLUG.sub("-", topic.lower()).strip("-") or "lesson"


def draft_basename(topic: str, level: CEFRLevel, created_at: datetime) -> str:
    """e.g. `ordering-coffee_B1_20260101-120000` — the stem shared by the draft
    markdown, its narration mp3 and its rendered mp4."""
    return f"{slugify(topic)}_{level}_{created_at.strftime(TIMESTAMP_FORMAT)}"
