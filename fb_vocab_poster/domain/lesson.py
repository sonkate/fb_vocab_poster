"""The core entities: a vocabulary lesson and the words it teaches."""
import re
from dataclasses import dataclass, field
from typing import Iterator, List, Sequence, Tuple

from .errors import IncompleteLessonError
from .lesson_format import FORMATS, LessonFormat
from .level import CEFRLevel

_BOLD_SPAN = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)


@dataclass(frozen=True)
class Fragment:
    """A run of paragraph text drawn as one piece, and whether it is a taught
    word. Punctuation sits in its own fragment so `**brother**.` colours the
    word without dragging the full stop in with it; `starts_word` is false for
    that full stop, which is how a renderer knows not to space it away from the
    word it follows."""

    text: str
    highlighted: bool = False
    starts_word: bool = True


@dataclass(frozen=True)
class VocabEntry:
    """One row of a lesson: three fields whose meaning the format decides.

    The names below are the vocab format's — word, pronunciation, meaning —
    because that format came first. A `mistake` row puts the wrong sentence,
    the corrected one and the explanation in the same three slots. Anything
    that is not format-specific should read them through `columns`.
    """

    word: str
    ipa: str = ""
    meaning: str = ""

    @property
    def columns(self):
        """The three fields positionally, for code that must not assume a format."""
        return self.word, self.ipa, self.meaning

    @property
    def spoken(self) -> str:
        """The text handed to a speech synthesiser."""
        return self.word.strip()


@dataclass(frozen=True)
class Lesson:
    """A complete, reviewed lesson: its rows, the paragraph that uses them if
    the format has one, and the caption that goes out with the post."""

    topic: str
    level: CEFRLevel
    vocab: Sequence[VocabEntry] = field(default_factory=tuple)
    paragraph: str = ""
    caption: str = ""
    format: LessonFormat = LessonFormat.VOCAB

    @property
    def spec(self):
        return FORMATS[self.format]

    def ensure_publishable(self) -> None:
        """Raises unless the lesson has everything its format needs."""
        spec = self.spec
        missing = []
        if spec.needs_paragraph and not self.paragraph.strip():
            missing.append("Paragraph")
        if not self.vocab:
            missing.append(spec.section)
        if missing:
            raise IncompleteLessonError(
                f"Lesson is missing a {' and '.join(missing)} section — check the draft file."
            )

    @property
    def post_text(self) -> str:
        """What a social post should say: the caption, or the paragraph if the
        caption was left empty."""
        return self.caption.strip() or self.plain_paragraph.strip()

    @property
    def plain_paragraph(self) -> str:
        """The paragraph without its bold markers, for anything that reads it
        aloud or posts it as text rather than drawing it."""
        return strip_markup(self.paragraph)

    def highlight_paragraph(self) -> Iterator[Fragment]:
        """Splits the paragraph into fragments, carrying through which ones the
        draft marked with `**`.

        The markup is the author's decision and this only reads it: a word the
        draft bolded once is taught once even where it appears again later, and
        a word that is in the vocab list but was left unmarked stays plain.
        """
        return fragments_of(self.paragraph)


def fragments_of(text: str) -> Iterator[Fragment]:
    """Splits any `**`-marked text into fragments, carrying through which
    words the author highlighted. Shared by the paragraph and by a `mistake`
    row's wrong/right columns, so every format that highlights individual
    words inside a longer text uses the same authoring convention."""
    starts_word = True
    for chunk, highlighted in _bold_runs(text):
        if chunk[:1].isspace():
            starts_word = True
        for index, piece in enumerate(chunk.split()):
            yield Fragment(piece, highlighted, starts_word or index > 0)
            starts_word = False
        if chunk[-1:].isspace():
            starts_word = True


def strip_markup(text: str) -> str:
    """The plain reading of `**`-marked text, for anything that speaks or
    posts it rather than drawing it."""
    return _BOLD_SPAN.sub(r"\1", text).replace("**", "")


def _bold_runs(text: str) -> Iterator[Tuple[str, bool]]:
    """The text as alternating plain and bolded stretches, markers removed."""
    cursor = 0
    for match in _BOLD_SPAN.finditer(text):
        if match.start() > cursor:
            yield text[cursor:match.start()], False
        yield match.group(1), True
        cursor = match.end()
    if cursor < len(text):
        yield text[cursor:], False


def to_entries(rows: List[dict]) -> Tuple[VocabEntry, ...]:
    """Convenience for adapters parsing loosely-typed vocab rows."""
    return tuple(
        VocabEntry(
            word=row.get("word", "").strip(),
            ipa=row.get("ipa", "").strip(),
            meaning=row.get("meaning", "").strip(),
        )
        for row in rows
        if row.get("word", "").strip()
    )
