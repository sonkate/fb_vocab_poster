"""What kind of lesson a draft is, and everything that follows from it.

A topic is not a unit of content — a *format* is. The same "Job interviews"
yields five words to learn, five mistakes to correct, or five weak phrases to
upgrade, and none of those repeats a single line of the others. That is the
difference between a hundred posts and a couple of thousand.

A format decides four things: what the three columns of a row mean, which
slide layout draws a row, which column is read aloud, and whether a paragraph
is part of the lesson at all. They are declared once in `FORMATS`; adding a
format means adding an entry there and a layout in the painter, and nothing
else in the pipeline branches on a format name.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple

from .errors import InvalidLessonFile

# Slide kinds. A row's kind is its format's layout, so the renderer can stay
# a lookup rather than a chain of format checks.
WORD = "word"
MISTAKE = "mistake"
UPGRADE = "upgrade"
PARAGRAPH = "paragraph"
OUTRO = "outro"
HOOK = "hook"


class LessonFormat(str, Enum):
    """Inherits `str` so it serialises as its own name in frontmatter."""

    VOCAB = "vocab"
    MISTAKE = "mistake"
    UPGRADE = "upgrade"

    @classmethod
    def parse(cls, raw: str) -> "LessonFormat":
        """Accepts any casing a human might type; blank means the original
        vocabulary format, so drafts written before formats existed still load."""
        text = str(raw).strip().lower()
        if not text:
            return cls.VOCAB
        try:
            return cls(text)
        except ValueError:
            raise InvalidLessonFile(
                f"format must be one of {', '.join(f.value for f in cls)} (got {raw!r})"
            ) from None

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FormatSpec:
    section: str                     # markdown heading holding the rows
    columns: Tuple[str, str, str]    # what a row's three fields mean
    slide_kind: str
    spoken_column: int               # which column the narrator reads
    repeat_slowly: bool              # read it slowly first, then at speed
    needs_paragraph: bool
    series_label: str = ""           # the show's name, worn at the foot of every slide

    # The "before/after" rhythm: read the first sentence, a stinger, read the
    # second one, another stinger, then hold for the explanation — spread
    # across two slides per row instead of one. `mistake` and `upgrade` both
    # ask for it; `spoken_column` and `repeat_slowly` are unused for a format
    # that sets this.
    contrast_rhythm: bool = False

    # Which stinger plays after each half — a name the audio composer looks
    # up, not a sound the domain knows how to make. "" means silence instead.
    # `mistake` and `upgrade` both use "buzz"/"ding": the user chose one
    # consistent audio signature across formats over signalling "weak" and
    # "wrong" differently, even though the field stays per-format in case a
    # future one genuinely needs its own sound.
    contrast_from_stinger: str = ""
    contrast_to_stinger: str = ""

    # Plays as the opening hook slide when a draft leaves `hook:` blank in its
    # frontmatter — every format needs one, since the hook slide now runs
    # before all of them, not just this one's content.
    default_hook: str = ""

    def series_caption(self, topic: str = "") -> str:
        """What the foot of a slide reads: the series, plus the topic of this
        particular episode when there is one."""
        topic = topic.strip().lower()
        if not (self.series_label and topic):
            return self.series_label or topic
        return f"{self.series_label} · {topic}"


FORMATS: Dict[LessonFormat, FormatSpec] = {
    LessonFormat.VOCAB: FormatSpec(
        section="Vocabulary",
        columns=("word", "ipa", "meaning"),
        slide_kind=WORD,
        spoken_column=0,
        repeat_slowly=True,
        needs_paragraph=True,
        series_label="5 từ mỗi ngày",
        default_hook="Nói tiếng Anh nghe như người bản xứ",
    ),
    LessonFormat.MISTAKE: FormatSpec(
        section="Mistakes",
        columns=("wrong", "right", "why"),
        slide_kind=MISTAKE,
        spoken_column=1,
        repeat_slowly=False,
        needs_paragraph=False,
        series_label="Sai chỗ nào",
        contrast_rhythm=True,
        contrast_from_stinger="buzz",
        contrast_to_stinger="ding",
        default_hook="Bạn có đang mắc lỗi này không?",
    ),
    LessonFormat.UPGRADE: FormatSpec(
        section="Upgrades",
        columns=("weak", "strong", "note"),
        slide_kind=UPGRADE,
        spoken_column=1,
        repeat_slowly=False,
        needs_paragraph=False,
        series_label="Đừng nói · nói",
        contrast_rhythm=True,
        contrast_from_stinger="buzz",
        contrast_to_stinger="ding",
        default_hook="Cách nói này nghe sang hơn hẳn",
    ),
}


def spec_for(lesson_format: LessonFormat) -> FormatSpec:
    return FORMATS[lesson_format]
