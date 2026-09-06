"""The drafts folder is itself the record of what has already been taught."""
from datetime import datetime

from fb_vocab_poster.domain import CEFRLevel, Lesson, LessonFormat, VocabEntry
from fb_vocab_poster.infrastructure.content import (
    MarkdownDraftRepository,
    markdown_format,
)
from fb_vocab_poster.infrastructure.ledger import DraftFolderLedger

FAMILY_A1 = """---
topic: Family
level: A1
format: vocab
---

## Vocabulary
<!-- word — ipa — meaning -->
- mother — /ˈmʌðər/ — a woman who has a child
- father — /ˈfɑːðər/ — a man who has a child

## Paragraph
My **mother** and my **father**.

## Caption
Level: A1
"""

FAMILY_A2 = FAMILY_A1.replace("level: A1", "level: A2").replace("mother", "cousin")
TRAVEL_B1 = FAMILY_A1.replace("topic: Family", "topic: Travel").replace(
    "level: A1", "level: B1"
)


def _write(tmp_path, name, text):
    (tmp_path / name).write_text(text, encoding="utf-8")


def test_it_collects_the_words_a_topic_and_level_already_taught(tmp_path):
    _write(tmp_path, "family_A1.md", FAMILY_A1)

    taught = DraftFolderLedger(drafts_dir=str(tmp_path)).taught("Family", CEFRLevel.A1)

    assert taught == {"mother", "father"}


def test_it_ignores_the_same_topic_at_another_level(tmp_path):
    _write(tmp_path, "family_A1.md", FAMILY_A1)
    _write(tmp_path, "family_A2.md", FAMILY_A2)

    ledger = DraftFolderLedger(drafts_dir=str(tmp_path))

    assert ledger.taught("Family", CEFRLevel.A1) == {"mother", "father"}
    assert "mother" not in ledger.taught("Family", CEFRLevel.A2)


def test_it_ignores_another_topic_at_the_same_level(tmp_path):
    _write(tmp_path, "travel_B1.md", TRAVEL_B1)

    assert DraftFolderLedger(drafts_dir=str(tmp_path)).taught(
        "Family", CEFRLevel.B1
    ) == set()


def test_the_topic_is_matched_however_it_was_typed(tmp_path):
    _write(tmp_path, "family_A1.md", FAMILY_A1)

    assert DraftFolderLedger(drafts_dir=str(tmp_path)).taught(
        "  fAmIlY ", CEFRLevel.A1
    ) == {"mother", "father"}


def test_a_broken_draft_does_not_stop_the_next_lesson(tmp_path):
    _write(tmp_path, "family_A1.md", FAMILY_A1)
    _write(tmp_path, "broken.md", "no frontmatter at all")

    assert DraftFolderLedger(drafts_dir=str(tmp_path)).taught("Family", CEFRLevel.A1)


def test_an_empty_folder_excludes_nothing(tmp_path):
    assert DraftFolderLedger(drafts_dir=str(tmp_path)).taught(
        "Family", CEFRLevel.A1
    ) == set()


def test_a_saved_draft_shows_the_avoid_list_without_parsing_it_back_as_content(
    tmp_path,
):
    lesson = Lesson(
        topic="Family",
        level=CEFRLevel.A1,
        format=LessonFormat.VOCAB,
        vocab=(VocabEntry("aunt", "/ɑːnt/", "your parent's sister"),),
        paragraph="My **aunt**.",
        caption="Level: A1",
    )

    ref = MarkdownDraftRepository(drafts_dir=str(tmp_path)).save(
        lesson, datetime(2026, 1, 1), avoid=["mother", "father"]
    )
    text = open(ref.identifier, encoding="utf-8").read()

    assert markdown_format.AVOID_NOTE in text
    assert "mother, father" in text
    assert markdown_format.parse(text).vocab == lesson.vocab


class StubLedger:
    def __init__(self, words):
        self.words = set(words)
        self.recorded = []

    def taught(self, topic, level):
        return set(self.words)

    def record(self, lesson, ref):
        self.recorded.append(ref)


def test_combining_ledgers_unions_what_each_one_remembers():
    from fb_vocab_poster.infrastructure.ledger import CombinedLedger

    combined = CombinedLedger(
        ledgers=(StubLedger({"mother"}), StubLedger({"father", "mother"}))
    )

    assert combined.taught("Family", CEFRLevel.A1) == {"mother", "father"}


def test_a_recorded_lesson_reaches_every_ledger():
    from fb_vocab_poster.application.ports import DraftRef
    from fb_vocab_poster.infrastructure.ledger import CombinedLedger

    first, second = StubLedger(()), StubLedger(())
    ref = DraftRef(identifier="drafts/family_A1.md", basename="family_A1")

    CombinedLedger(ledgers=(first, second)).record(
        Lesson(topic="Family", level=CEFRLevel.A1), ref
    )

    assert first.recorded == [ref] and second.recorded == [ref]


def test_without_credentials_the_container_reads_the_drafts_folder_alone():
    from fb_vocab_poster.container import Container
    from fb_vocab_poster.infrastructure.config import Settings
    from fb_vocab_poster.infrastructure.ledger import DraftFolderLedger

    ledger = Container(settings=Settings(firestore_credentials="")).ledger

    assert isinstance(ledger, DraftFolderLedger)


def test_with_credentials_the_container_reads_both_without_opening_a_connection():
    from fb_vocab_poster.container import Container
    from fb_vocab_poster.infrastructure.config import Settings
    from fb_vocab_poster.infrastructure.ledger import (
        CombinedLedger,
        DraftFolderLedger,
        FirestoreVocabularyLedger,
    )

    ledger = Container(settings=Settings(firestore_credentials="/nowhere.json")).ledger

    assert isinstance(ledger, CombinedLedger)
    assert [type(l) for l in ledger.ledgers] == [
        DraftFolderLedger,
        FirestoreVocabularyLedger,
    ]
