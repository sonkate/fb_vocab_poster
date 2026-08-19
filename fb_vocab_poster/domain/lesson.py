"""The core entities: a vocabulary lesson and the words it teaches."""
import re
from dataclasses import dataclass, field
from typing import Iterator, List, Sequence, Tuple

from .errors import IncompleteLessonError
from .level import CEFRLevel

_WORD_CHARS = re.compile(r"[^\w']")


@dataclass(frozen=True)
class VocabEntry:
    """One word being taught, with how to say it and what it means."""

    word: str
    ipa: str = ""
    meaning: str = ""

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
    """A complete, reviewed lesson: the words, the paragraph that uses them,
    and the caption that goes out with the post."""

    topic: str
    level: CEFRLevel
    vocab: Sequence[VocabEntry] = field(default_factory=tuple)
    paragraph: str = ""
    caption: str = ""

    def ensure_publishable(self) -> None:
        """Raises unless the lesson has everything the pipeline needs."""
        missing = []
        if not self.paragraph.strip():
            missing.append("Paragraph")
        if not self.vocab:
            missing.append("Vocabulary")
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
