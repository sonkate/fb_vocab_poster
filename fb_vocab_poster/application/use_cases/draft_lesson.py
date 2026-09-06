"""Use case: turn a topic + level into a draft a human can edit."""
from dataclasses import dataclass
from typing import List

from ...domain import CEFRLevel, Lesson, LessonFormat, spec_for
from ..ports import Clock, DraftRef, DraftRepository, LessonDrafter, VocabularyLedger


def _is_blank_form(lesson: Lesson) -> bool:
    """True when every row is still the column legend the template lays down.

    A blank form has taught nobody anything, so recording its rows would put
    the literal words "word", "ipa" and "meaning" into the ledger and exclude
    them from every future lesson.
    """
    columns = spec_for(lesson.format).columns
    return bool(lesson.vocab) and all(
        entry.columns == columns for entry in lesson.vocab
    )


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

        if not _is_blank_form(lesson):
            self.ledger.record(lesson, ref)
        return ref
