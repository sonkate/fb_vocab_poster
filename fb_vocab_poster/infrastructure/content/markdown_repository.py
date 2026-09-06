"""Stores drafts as markdown files under `drafts/`.

Implements `application.ports.DraftRepository`. The identifier a caller passes
around is simply the file path, which keeps the CLI's copy-paste workflow
(`python main.py build drafts/travel_B1_....md`) working unchanged.
"""
import glob
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from ...application.ports import DraftRef
from ...domain import InvalidLessonFile, Lesson
from ...domain.naming import draft_basename
from . import markdown_format


@dataclass(frozen=True)
class MarkdownDraftRepository:
    drafts_dir: str

    def save(
        self, lesson: Lesson, created_at: datetime, avoid: Sequence[str] = ()
    ) -> DraftRef:
        os.makedirs(self.drafts_dir, exist_ok=True)
        basename = draft_basename(lesson.topic, lesson.level, created_at)
        path = os.path.join(self.drafts_dir, f"{basename}.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(markdown_format.render(lesson, avoid=avoid))
        return DraftRef(identifier=path, basename=basename)

    def load(self, identifier: str) -> Lesson:
        try:
            with open(identifier, "r", encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            raise InvalidLessonFile(f"Could not read draft {identifier}: {exc}") from exc
        return markdown_format.parse(text, source=identifier)

    def identifiers(self) -> Sequence[str]:
        """Every draft on disk, oldest name first — the basenames start with
        the topic and end with a timestamp, so sorting is chronological."""
        return sorted(glob.glob(os.path.join(self.drafts_dir, "*.md")))

    def reference(self, identifier: str) -> DraftRef:
        basename = os.path.splitext(os.path.basename(identifier))[0]
        return DraftRef(identifier=identifier, basename=basename)

    def modified_at(self, identifier: str) -> datetime:
        return datetime.fromtimestamp(os.path.getmtime(identifier))
