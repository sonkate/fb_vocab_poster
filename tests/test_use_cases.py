"""The use cases are exercised with fakes only — no gTTS, no moviepy, no HTTP.
That is the point of the port boundary."""
from datetime import datetime

import pytest

from fb_vocab_poster.application import (
    BackfillLedger,
    DraftLesson,
    PublishLesson,
    RenderLesson,
)
from fb_vocab_poster.application.ports import (
    DraftRef,
    Narration,
    PublishReceipt,
)
from fb_vocab_poster.domain import (
    CEFRLevel,
    IncompleteLessonError,
    Lesson,
    LessonFormat,
    NarrationSegment,
    VocabEntry,
)

LESSON = Lesson(
    topic="Travel",
    level=CEFRLevel.B1,
    vocab=(VocabEntry(word="platform"),),
    paragraph="Wait on the platform.",
    caption="Level: B1 #travel",
)


class FakeRepository:
    def __init__(self, lesson=LESSON):
        self.lesson = lesson
        self.saved = []
        self.avoided = []

    def save(self, lesson, created_at, avoid=()):
        self.saved.append((lesson, created_at))
        self.avoided.append(tuple(avoid))
        return DraftRef(identifier="drafts/travel_B1.md", basename="travel_B1")

    def load(self, identifier):
        return self.lesson

    def reference(self, identifier):
        return DraftRef(identifier=identifier, basename="travel_B1")

    def identifiers(self):
        return ["drafts/travel_B1.md"]


class FakeDrafter:
    def __init__(self, lesson=LESSON):
        self.lesson = lesson
        self.calls = []
        self.avoided = []

    def draft(self, topic, level, lesson_format, avoid=()):
        self.calls.append((topic, level, lesson_format))
        self.avoided.append(tuple(avoid))
        return self.lesson


class FakeLedger:
    def __init__(self, taught=()):
        self._taught = set(taught)
        self.recorded = []

    def taught(self, topic, level):
        return set(self._taught)

    def record(self, lesson, ref):
        self.recorded.append((lesson, ref))


class FakeNarrator:
    def compose(self, lesson, ref):
        return Narration(
            audio_path=f"output/{ref.basename}.mp3",
            segments=(NarrationSegment(kind="paragraph", duration=4.0),),
        )


class FakeVideoRenderer:
    def render(self, lesson, narration, ref):
        return f"output/{ref.basename}.mp4"


class FakePublisher:
    def __init__(self):
        self.posted = []

    def publish(self, video_path, message):
        self.posted.append((video_path, message))
        return PublishReceipt(post_id="99")


class FakeClock:
    def now(self):
        return datetime(2026, 1, 1, 12, 0, 0)


class SilentReporter:
    def __init__(self):
        self.messages = []

    def step(self, message):
        self.messages.append(message)


def make_draft(drafter=None, repository=None, ledger=None):
    return DraftLesson(
        drafter=drafter or FakeDrafter(),
        repository=repository or FakeRepository(),
        clock=FakeClock(),
        ledger=ledger or FakeLedger(),
    )


def make_render(repository=None):
    return RenderLesson(
        repository=repository or FakeRepository(),
        narrator=FakeNarrator(),
        video_renderer=FakeVideoRenderer(),
        reporter=SilentReporter(),
    )


def test_drafting_parses_the_level_before_asking_the_drafter():
    drafter, repository = FakeDrafter(), FakeRepository()

    ref = make_draft(drafter=drafter, repository=repository)("Travel", "b1")

    assert drafter.calls == [("Travel", CEFRLevel.B1, LessonFormat.VOCAB)]
    assert repository.saved[0][1] == datetime(2026, 1, 1, 12, 0, 0)
    assert ref.identifier == "drafts/travel_B1.md"


def test_the_requested_format_reaches_the_drafter():
    drafter = FakeDrafter()

    make_draft(drafter=drafter)("Travel", "b1", "mistake")

    assert drafter.calls[0][2] is LessonFormat.MISTAKE


def test_rendering_returns_the_lesson_alongside_its_artefacts():
    rendered = make_render()("drafts/travel_B1.md")

    assert rendered.lesson == LESSON
    assert rendered.video_path == "output/travel_B1.mp4"
    assert rendered.narration.audio_path == "output/travel_B1.mp3"


def test_rendering_refuses_an_unfinished_draft_before_synthesising_anything():
    empty = Lesson(topic="Travel", level=CEFRLevel.B1)

    with pytest.raises(IncompleteLessonError):
        make_render(FakeRepository(lesson=empty))("drafts/travel_B1.md")


def test_publishing_sends_the_rendered_video_with_the_lesson_caption():
    publisher = FakePublisher()

    rendered, receipt = PublishLesson(
        render=make_render(), publisher=publisher, reporter=SilentReporter()
    )("drafts/travel_B1.md")

    assert publisher.posted == [("output/travel_B1.mp4", "Level: B1 #travel")]
    assert receipt.post_id == "99"
    assert rendered.video_path == "output/travel_B1.mp4"


def test_words_already_taught_are_handed_to_the_drafter_to_avoid():
    drafter = FakeDrafter()
    ledger = FakeLedger(taught={"mother", "father", "sister"})

    make_draft(drafter=drafter, ledger=ledger)("Family", "a1")

    assert drafter.avoided == [("father", "mother", "sister")]


def test_the_avoid_list_also_reaches_the_draft_file():
    repository = FakeRepository()
    ledger = FakeLedger(taught={"mother", "father"})

    make_draft(repository=repository, ledger=ledger)("Family", "a1")

    assert repository.avoided == [("father", "mother")]


def test_a_finished_draft_is_recorded_so_the_next_lesson_skips_its_words():
    ledger = FakeLedger()

    ref = make_draft(ledger=ledger)("Travel", "b1")

    assert [(lesson, r.basename) for lesson, r in ledger.recorded] == [
        (LESSON, "travel_B1")
    ]
    assert ref.basename == "travel_B1"


def test_a_blank_template_is_not_recorded_as_though_it_taught_anything():
    blank = Lesson(
        topic="Family",
        level=CEFRLevel.A1,
        vocab=(VocabEntry("word", "ipa", "meaning"),),
        paragraph="Paste your paragraph here.",
    )
    ledger = FakeLedger()

    make_draft(drafter=FakeDrafter(lesson=blank), ledger=ledger)("Family", "a1")

    assert ledger.recorded == []


BLANK = Lesson(
    topic="Family",
    level=CEFRLevel.A1,
    vocab=(VocabEntry("word", "ipa", "meaning"),),
    paragraph="Paste your paragraph here.",
)


class FolderRepository:
    """A repository holding several drafts, one of which cannot be read."""

    def __init__(self, lessons):
        self.lessons = dict(lessons)

    def identifiers(self):
        return sorted(self.lessons)

    def reference(self, identifier):
        return DraftRef(identifier=identifier, basename=identifier)

    def load(self, identifier):
        lesson = self.lessons[identifier]
        if lesson is None:
            raise OSError("unreadable draft")
        return lesson

    def save(self, lesson, created_at, avoid=()):
        raise AssertionError("backfill must never write a draft")


def make_backfill(lessons, ledger):
    return BackfillLedger(
        repository=FolderRepository(lessons),
        ledger=ledger,
        reporter=SilentReporter(),
    )


def test_backfill_records_every_readable_draft():
    ledger = FakeLedger()

    report = make_backfill({"family_A1": LESSON, "travel_B1": LESSON}, ledger)()

    assert report.recorded == ("family_A1", "travel_B1")
    assert [ref.basename for _, ref in ledger.recorded] == ["family_A1", "travel_B1"]


def test_backfill_skips_a_blank_template_rather_than_teaching_its_placeholders():
    ledger = FakeLedger()

    report = make_backfill({"blank_A1": BLANK, "travel_B1": LESSON}, ledger)()

    assert report.recorded == ("travel_B1",)
    assert report.skipped == (("blank_A1", "still a blank template"),)


def test_one_unreadable_draft_does_not_abandon_the_others():
    ledger = FakeLedger()

    report = make_backfill({"broken": None, "travel_B1": LESSON}, ledger)()

    assert report.recorded == ("travel_B1",)
    assert report.skipped[0][0] == "broken"
    assert report.total == 2


def test_backfilling_twice_records_the_same_drafts_again_not_new_ones():
    ledger = FakeLedger()
    backfill = make_backfill({"family_A1": LESSON}, ledger)

    first, second = backfill(), backfill()

    assert first.recorded == second.recorded == ("family_A1",)
    # Same reference both times, so a keyed store overwrites instead of adding.
    assert {ref.basename for _, ref in ledger.recorded} == {"family_A1"}
