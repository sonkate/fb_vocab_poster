"""Asks several ledgers at once.

Turning Firestore on must not lose what is already on disk: `drafts/` holds
every lesson written before the database existed, so the two are read together
and the union is what a topic has taught.
"""
from dataclasses import dataclass
from typing import Sequence, Set

from ...application.ports import DraftRef, VocabularyLedger
from ...domain import CEFRLevel, Lesson


@dataclass(frozen=True)
class CombinedLedger:
    ledgers: Sequence[VocabularyLedger]

    def taught(self, topic: str, level: CEFRLevel) -> Set[str]:
        words: Set[str] = set()
        for ledger in self.ledgers:
            words |= ledger.taught(topic, level)
        return words

    def record(self, lesson: Lesson, ref: DraftRef) -> None:
        for ledger in self.ledgers:
            ledger.record(lesson, ref)
