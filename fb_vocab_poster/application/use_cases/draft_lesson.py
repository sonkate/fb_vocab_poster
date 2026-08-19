"""Use case: turn a topic + level into a draft a human can edit."""
from dataclasses import dataclass

from ...domain import CEFRLevel
from ..ports import Clock, DraftRef, DraftRepository, LessonDrafter


@dataclass(frozen=True)
class DraftLesson:
    drafter: LessonDrafter
    repository: DraftRepository
    clock: Clock

    def __call__(self, topic: str, level: str) -> DraftRef:
        parsed_level = CEFRLevel.parse(level)
        lesson = self.drafter.draft(topic, parsed_level)
        return self.repository.save(lesson, self.clock.now())
