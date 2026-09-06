"""Reads the taught-word history straight out of `drafts/`.

Implements `application.ports.VocabularyLedger` for the no-credential path.
Every word this system has ever taught is already sitting in a draft file
alongside its topic and level, so the folder is a complete ledger on its own —
Firestore makes that history queryable from elsewhere, it does not create it.
"""
import glob
import os
from dataclasses import dataclass
from typing import Dict, Set

from ...application.ports import DraftRef
from ...domain import CEFRLevel, DomainError, Lesson
from ..content import markdown_format


def normalise_topic(topic: str) -> str:
    """Topics are typed by hand on the CLI, so "Family" and " family " match."""
    return topic.strip().lower()


@dataclass(frozen=True)
class DraftFolderLedger:
    drafts_dir: str

    def taught(self, topic: str, level: CEFRLevel) -> Set[str]:
        wanted = normalise_topic(topic)
        seen: Dict[str, str] = {}
        for path in sorted(glob.glob(os.path.join(self.drafts_dir, "*.md"))):
            lesson = self._read(path)
            if lesson is None:
                continue
            if normalise_topic(lesson.topic) != wanted or lesson.level is not level:
                continue
            for entry in lesson.vocab:
                word = entry.word.strip()
                if word:
                    # Keyed case-insensitively so "Mother" and "mother" are one
                    # word, but the spelling the draft used is what is returned.
                    seen.setdefault(word.lower(), word)
        return set(seen.values())

    def record(self, lesson: Lesson, ref: DraftRef) -> None:
        """Nothing to do: the draft file the repository just wrote is the record."""

    @staticmethod
    def _read(path: str):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return markdown_format.parse(handle.read(), source=path)
        except (OSError, DomainError):
            # A half-written or hand-broken draft must not stop the next lesson.
            return None
