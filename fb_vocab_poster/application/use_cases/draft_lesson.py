"""Use case: turn a topic + level into a draft a human can edit."""
from dataclasses import dataclass

from ...domain import CEFRLevel, LessonFormat
from ..ports import Clock, DraftRef, DraftRepository, LessonDrafter


@dataclass(frozen=True)
class DraftLesson:
    drafter: LessonDrafter
    repository: DraftRepository
    clock: Clock

    def __call__(self, topic: str, level: str, lesson_format: str = "") -> DraftRef:
        lesson = self.drafter.draft(
            topic, CEFRLevel.parse(level), LessonFormat.parse(lesson_format)
        )
        return self.repository.save(lesson, self.clock.now())
