"""Use case: turn a topic + level into a draft a human can edit."""
from dataclasses import dataclass
from typing import List

from ...domain import CEFRLevel, LessonFormat
from ..blank_form import is_blank_form
from ..ports import Clock, DraftRef, DraftRepository, LessonDrafter, VocabularyLedger


@dataclass(frozen=True)
class DraftLesson:
    drafter: LessonDrafter
    repository: DraftRepository
    clock: Clock
    ledger: VocabularyLedger

    def __call__(self, topic: str, level: str, lesson_format: str = "") -> DraftRef:
        parsed_level = CEFRLevel.parse(level)
        avoid: List[str] = sorted(self.ledger.taught(topic, parsed_level))

        lesson = self.drafter.draft(
            topic, parsed_level, LessonFormat.parse(lesson_format), avoid=avoid
        )
        ref = self.repository.save(lesson, self.clock.now(), avoid=avoid)

        if not is_blank_form(lesson):
            self.ledger.record(lesson, ref)
        return ref
