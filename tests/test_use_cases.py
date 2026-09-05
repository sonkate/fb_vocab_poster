"""The use cases are exercised with fakes only — no gTTS, no moviepy, no HTTP.
That is the point of the port boundary."""
from datetime import datetime

import pytest

from fb_vocab_poster.application import DraftLesson, PublishLesson, RenderLesson
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

    def save(self, lesson, created_at):
        self.saved.append((lesson, created_at))
        return DraftRef(identifier="drafts/travel_B1.md", basename="travel_B1")

    def load(self, identifier):
        return self.lesson

    def reference(self, identifier):
        return DraftRef(identifier=identifier, basename="travel_B1")


class FakeDrafter:
    def __init__(self):
        self.calls = []

    def draft(self, topic, level, lesson_format):
        self.calls.append((topic, level, lesson_format))
        return LESSON


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


def make_render(repository=None):
    return RenderLesson(
        repository=repository or FakeRepository(),
        narrator=FakeNarrator(),
        video_renderer=FakeVideoRenderer(),
        reporter=SilentReporter(),
    )


def test_drafting_parses_the_level_before_asking_the_drafter():
    drafter, repository = FakeDrafter(), FakeRepository()

    ref = DraftLesson(drafter=drafter, repository=repository, clock=FakeClock())(
        "Travel", "b1"
    )

    assert drafter.calls == [("Travel", CEFRLevel.B1, LessonFormat.VOCAB)]
    assert repository.saved[0][1] == datetime(2026, 1, 1, 12, 0, 0)
    assert ref.identifier == "drafts/travel_B1.md"


def test_the_requested_format_reaches_the_drafter():
    drafter = FakeDrafter()

    DraftLesson(drafter=drafter, repository=FakeRepository(), clock=FakeClock())(
        "Travel", "b1", "mistake"
    )

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
