"""Drafts an empty lesson for hand-filling.

Implements `application.ports.LessonDrafter` for the no-API-key path: the user
pastes in content from a free Claude chat instead of paying per token. The file
that lands on disk is identical in shape to the AI-drafted one.
"""
from dataclasses import dataclass
from typing import Sequence

from ...domain import CEFRLevel, Lesson, LessonFormat, VocabEntry, spec_for

PLACEHOLDER_PARAGRAPH = "Paste your paragraph here. Use every word above at least once."
PLACEHOLDER_CAPTION = "Paste your Facebook caption here."


@dataclass(frozen=True)
class TemplateDrafter:
    rows: int = 2

    def draft(
        self,
        topic: str,
        level: CEFRLevel,
        lesson_format: LessonFormat = LessonFormat.VOCAB,
        avoid: Sequence[str] = (),
    ) -> Lesson:
        # `avoid` is deliberately unused here. A blank form has no words to
        # choose, so the already-taught list is of no use to this drafter —
        # it reaches the person filling the form in as a comment the
        # repository writes into the file itself.
        # Each placeholder row spells out that format's own column names, so a
        # blank file says what belongs where without a trip back to the README.
        columns = spec_for(lesson_format).columns
        return Lesson(
            topic=topic,
            level=level,
            format=lesson_format,
            vocab=tuple(VocabEntry(*columns) for _ in range(self.rows)),
            paragraph=PLACEHOLDER_PARAGRAPH,
            caption=PLACEHOLDER_CAPTION,
        )
