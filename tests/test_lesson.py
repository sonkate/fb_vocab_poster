import pytest

from fb_vocab_poster.domain import (
    CEFRLevel,
    IncompleteLessonError,
    InvalidLevelError,
    Lesson,
    VocabEntry,
)


def test_level_parsing_accepts_what_a_human_types():
    assert CEFRLevel.parse(" b2 ") is CEFRLevel.B2


def test_unknown_level_is_rejected_with_the_valid_options():
    with pytest.raises(InvalidLevelError, match="A1"):
        CEFRLevel.parse("Z9")


def test_taught_words_are_flagged_inside_the_paragraph_despite_punctuation():
    lesson = Lesson(
        topic="School",
        level=CEFRLevel.B1,
        vocab=(VocabEntry(word="Homework"),),
        paragraph="I finished homework, then rested.",
    )

    assert list(lesson.highlight_paragraph()) == [
        ("I", False),
        ("finished", False),
        ("homework,", True),
        ("then", False),
        ("rested.", False),
    ]


def test_post_text_falls_back_to_the_paragraph_when_no_caption_was_written():
    lesson = Lesson(
        topic="School", level=CEFRLevel.B1, paragraph="A short lesson.", caption="  "
    )

    assert lesson.post_text == "A short lesson."


def test_a_lesson_missing_its_paragraph_and_vocab_cannot_be_published():
    with pytest.raises(IncompleteLessonError, match="Paragraph and Vocabulary"):
        Lesson(topic="School", level=CEFRLevel.B1).ensure_publishable()
