"""How a lesson is read aloud.

The *plan* (what is spoken, in what order, at what speed) is pure policy and
lives here. The *timeline* (how long each part actually took) can only be known
after real speech is synthesised, so adapters build it — but its shape is
defined here too, because the video layer reasons about it.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .lesson import Lesson, VocabEntry
from .lesson_format import OUTRO, PARAGRAPH, WORD


@dataclass(frozen=True)
class SpeechCue:
    """A single thing to say: `text`, spoken slowly or at normal speed."""

    kind: str
    text: str
    slow: bool = False
    vocab_index: Optional[int] = None

    @property
    def clip_name(self) -> str:
        """Stable filename stem, so re-runs overwrite rather than pile up."""
        if self.kind == WORD:
            return f"word_{self.vocab_index}_{'slow' if self.slow else 'normal'}"
        return self.kind


@dataclass(frozen=True)
class NarrationTiming:
    """Pacing policy for the narration, in seconds."""

    # The brand card runs after the lesson, not before it: the opening
    # seconds decide whether a viewer stays, and a static title spends them.
    outro_pause: float = 2.2
    pause_between_slow_fast: float = 0.5
    pause_after_word: float = 0.8


@dataclass(frozen=True)
class NarrationSegment:
    """One stretch of the finished narration, and how long it runs. The video
    layer sizes each slide from these so picture and sound never drift."""

    kind: str
    duration: float
    vocab: Optional[VocabEntry] = None


def build_audio_plan(lesson: Lesson) -> List[SpeechCue]:
    """What gets read aloud, in order, at what pace.

    The format decides which column is spoken and whether it is worth hearing
    twice: a vocabulary word is read slowly and then at speed so a learner
    catches it in isolation, while a corrected sentence only needs saying once.
    """
    spec = lesson.spec
    plan: List[SpeechCue] = []
    for index, entry in enumerate(lesson.vocab):
        text = entry.columns[spec.spoken_column].strip()
        if spec.repeat_slowly:
            plan.append(SpeechCue(kind=WORD, text=text, slow=True, vocab_index=index))
        plan.append(SpeechCue(kind=WORD, text=text, slow=False, vocab_index=index))
    if spec.needs_paragraph:
        plan.append(SpeechCue(kind=PARAGRAPH, text=lesson.plain_paragraph.strip(), slow=False))
    return plan


def word_segment_duration(slow_seconds: float, fast_seconds: float, timing: NarrationTiming) -> float:
    """How long one vocabulary word occupies the screen: both readings plus the
    breathing room around them."""
    return slow_seconds + timing.pause_between_slow_fast + fast_seconds + timing.pause_after_word


def total_duration(segments: Sequence[NarrationSegment]) -> float:
    return sum(segment.duration for segment in segments)
