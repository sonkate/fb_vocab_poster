"""How a lesson is read aloud.

The *plan* (what is spoken, in what order, at what speed) is pure policy and
lives here. The *timeline* (how long each part actually took) can only be known
after real speech is synthesised, so adapters build it — but its shape is
defined here too, because the video layer reasons about it.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .lesson import Lesson, VocabEntry, strip_markup
from .lesson_format import HOOK, OUTRO, PARAGRAPH, WORD


@dataclass(frozen=True)
class SpeechCue:
    """A single thing to say: `text`, spoken slowly or at normal speed, or —
    for a contrast-rhythm row — tagged by which half it is."""

    kind: str
    text: str
    slow: bool = False
    vocab_index: Optional[int] = None
    role: str = ""   # "" for a plain cue; "wrong"/"right" for a contrast row's two halves

    @property
    def clip_name(self) -> str:
        """Stable filename stem, so re-runs overwrite rather than pile up."""
        if self.kind == WORD:
            return f"word_{self.vocab_index}_{'slow' if self.slow else 'normal'}"
        if self.role:
            return f"{self.kind}_{self.vocab_index}_{self.role}"
        return self.kind


@dataclass(frozen=True)
class NarrationTiming:
    """Pacing policy for the narration, in seconds."""

    # The brand card runs after the lesson, not before it: the opening
    # seconds decide whether a viewer stays, and a static title spends them.
    outro_pause: float = 2.2
    pause_between_slow_fast: float = 0.5
    pause_after_word: float = 0.8

    # The opening hook slide: whatever the hook line's own reading takes,
    # plus a short beat before the first content slide cuts in.
    hook_pause: float = 0.4

    # The contrast rhythm (`mistake` only): wrong sentence, buzz, right
    # sentence, ding, then a hold sized to the Vietnamese explanation so a
    # viewer has time to actually read it before the next row starts.
    # The buzzer/ding stingers themselves run ~2s — matching the recorded
    # assets' full length. This overshoots the format's 35-45s target on its
    # own (5 rows x ~3.1s of extra SFX vs the original 0.45s stubs); the user
    # chose to keep both full-length and the reading pause untouched rather
    # than trim either, accepting a longer video.
    buzzer_duration: float = 2.0
    ding_duration: float = 2.0
    reading_pause_base: float = 0.6
    reading_seconds_per_word: float = 0.16


@dataclass(frozen=True)
class NarrationSegment:
    """One stretch of the finished narration, and how long it runs. The video
    layer sizes each slide from these so picture and sound never drift."""

    kind: str
    duration: float
    vocab: Optional[VocabEntry] = None
    stage: str = "full"   # "wrong" or "full" — only meaningful for a contrast-rhythm row split into two slides


def build_audio_plan(lesson: Lesson) -> List[SpeechCue]:
    """What gets read aloud, in order, at what pace.

    The format decides which column is spoken and whether it is worth hearing
    twice: a vocabulary word is read slowly and then at speed so a learner
    catches it in isolation, a corrected sentence only needs saying once, and
    a contrast-rhythm row reads both halves — the wrong sentence still gets
    read aloud, on purpose: a buzzer plus an on-screen "SAI" tag mark it as
    wrong the instant it's heard, so it teaches instead of misleading.
    """
    spec = lesson.spec
    plan: List[SpeechCue] = [SpeechCue(kind=HOOK, text=lesson.hook_line.strip())]
    for index, entry in enumerate(lesson.vocab):
        if spec.contrast_rhythm:
            wrong, right, _note = entry.columns
            plan.append(
                SpeechCue(
                    kind=spec.slide_kind,
                    text=strip_markup(wrong).strip(),
                    vocab_index=index,
                    role="wrong",
                )
            )
            plan.append(
                SpeechCue(
                    kind=spec.slide_kind,
                    text=strip_markup(right).strip(),
                    vocab_index=index,
                    role="right",
                )
            )
            continue
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
