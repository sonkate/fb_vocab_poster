"""Drafts an empty lesson for hand-filling.

Implements `application.ports.LessonDrafter` for the no-API-key path: the user
pastes in content from a free Claude chat instead of paying per token. The file
that lands on disk is identical in shape to the AI-drafted one.
"""
from dataclasses import dataclass

from ...domain import CEFRLevel, Lesson, VocabEntry

PLACEHOLDER_PARAGRAPH = "Paste your paragraph here. Use every vocab word above at least once."
PLACEHOLDER_CAPTION = "Paste your Facebook caption here."


@dataclass(frozen=True)
class TemplateDrafter:
    rows: int = 2

    def draft(self, topic: str, level: CEFRLevel) -> Lesson:
        return Lesson(
            topic=topic,
            level=level,
            vocab=tuple(
                VocabEntry(word="word", ipa="/ipa/", meaning="meaning")
                for _ in range(self.rows)
            ),
            paragraph=PLACEHOLDER_PARAGRAPH,
            caption=PLACEHOLDER_CAPTION,
        )
