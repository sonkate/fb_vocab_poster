"""The core entities: a vocabulary lesson and the words it teaches."""
import re
from dataclasses import dataclass, field
from typing import Iterator, List, Sequence, Tuple

from .errors import IncompleteLessonError
from .lesson_format import FORMATS, LessonFormat
from .level import CEFRLevel

_WORD_CHARS = re.compile(r"[^\w']")


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

    @property
    def lookup_key(self) -> str:
        """Normalised form used to spot this word inside the paragraph."""
        return self.word.strip().lower()


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
        return self.caption.strip() or self.paragraph.strip()

    @property
    def vocab_keys(self) -> frozenset:
        return frozenset(entry.lookup_key for entry in self.vocab)

    def highlight_paragraph(self) -> Iterator[Tuple[str, bool]]:
        """Walks the paragraph word by word, flagging the ones being taught so
        a renderer can colour them without re-deriving the rule."""
        keys = self.vocab_keys
        for token in self.paragraph.split():
            yield token, _WORD_CHARS.sub("", token).lower() in keys


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
