"""The boundary the use cases talk to.

Every port is a Protocol, so adapters satisfy them structurally — infrastructure
depends on the application layer, never the reverse. Swapping gTTS for
ElevenLabs, or Facebook for Instagram, means writing a new class that fits one
of these shapes and wiring it in the container; no use case changes.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol, Sequence, Set

from ..domain import (
    CEFRLevel,
    Lesson,
    LessonFormat,
    NarrationSegment,
    SpeechCue,
)


@dataclass(frozen=True)
class DraftRef:
    """Opaque handle to a stored draft, plus the stem its artefacts share."""

    identifier: str
    basename: str

    def __str__(self) -> str:
        return self.identifier


@dataclass(frozen=True)
class Narration:
    """A finished narration track and the timeline that describes it."""

    audio_path: str
    segments: Sequence[NarrationSegment]


@dataclass(frozen=True)
class RenderedLesson:
    """Everything `build` produces, and everything `publish` consumes."""

    lesson: Lesson
    narration: Narration
    video_path: str


@dataclass(frozen=True)
class PublishReceipt:
    """Proof that a post went out, as reported by the platform."""

    post_id: str
    raw: Optional[dict] = None


class LessonDrafter(Protocol):
    """Produces lesson content for a topic, level and format."""

    def draft(
        self,
        topic: str,
        level: CEFRLevel,
        lesson_format: LessonFormat,
        avoid: Sequence[str] = (),
    ) -> Lesson: ...


class DraftRepository(Protocol):
    """Persists reviewable drafts and reads the edited versions back."""

    def save(
        self, lesson: Lesson, created_at: datetime, avoid: Sequence[str] = ()
    ) -> DraftRef: ...

    def load(self, identifier: str) -> Lesson: ...

    def reference(self, identifier: str) -> DraftRef: ...

    def identifiers(self) -> Sequence[str]: ...


class VocabularyLedger(Protocol):
    """Remembers what a topic has already taught, so it is never taught twice.

    Five words do not exhaust a topic — Family at A1 has twenty more — so a
    second lesson on the same topic must know which words the first one used.
    """

    def taught(self, topic: str, level: CEFRLevel) -> Set[str]: ...

    def record(self, lesson: Lesson, ref: DraftRef) -> None: ...


class SpeechSynthesizer(Protocol):
    """Turns one cue into an audio file at `out_path`, returning that path."""

    def synthesize(self, cue: SpeechCue, out_path: str) -> str: ...


class NarrationComposer(Protocol):
    """Synthesises and stitches the lesson's full narration track."""

    def compose(self, lesson: Lesson, ref: DraftRef) -> Narration: ...


class VideoRenderer(Protocol):
    """Draws the slides and muxes them against the narration."""

    def render(self, lesson: Lesson, narration: Narration, ref: DraftRef) -> str: ...


class LessonPublisher(Protocol):
    """Posts a rendered video somewhere public."""

    def publish(self, video_path: str, message: str) -> PublishReceipt: ...


class Workspace(Protocol):
    """Decides where artefacts land, so no use case builds a path by hand."""

    def narration_audio(self, basename: str) -> str: ...

    def narration_workdir(self, basename: str) -> str: ...

    def video(self, basename: str) -> str: ...

    def slides_workdir(self, basename: str) -> str: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class ProgressReporter(Protocol):
    """Narrates long-running work to whoever started it."""

    def step(self, message: str) -> None: ...


__all__ = [
    "Clock",
    "DraftRef",
    "DraftRepository",
    "LessonDrafter",
    "LessonPublisher",
    "Narration",
    "NarrationComposer",
    "ProgressReporter",
    "PublishReceipt",
    "RenderedLesson",
    "SpeechSynthesizer",
    "VideoRenderer",
    "VocabularyLedger",
    "Workspace",
]
