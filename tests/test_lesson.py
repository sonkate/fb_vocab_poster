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


def _fragments(paragraph: str, *words: str):
    lesson = Lesson(
        topic="School",
        level=CEFRLevel.B1,
        vocab=tuple(VocabEntry(word=word) for word in words),
        paragraph=paragraph,
    )
    return [(f.text, f.highlighted, f.starts_word) for f in lesson.highlight_paragraph()]


def test_a_repeated_word_is_taught_only_where_the_draft_marked_it():
    assert _fragments("I did **homework**, then more homework.", "homework") == [
        ("I", False, True),
        ("did", False, True),
        ("homework", True, True),
        (",", False, False),
        ("then", False, True),
        ("more", False, True),
        ("homework.", False, True),
    ]


def test_punctuation_stays_outside_the_taught_word():
    # The full stop is its own fragment and does not begin a word, so it is
    # drawn in body colour hard up against `brother` with no gap.
    assert _fragments("I have one **brother**.", "brother") == [
        ("I", False, True),
        ("have", False, True),
        ("one", False, True),
        ("brother", True, True),
        (".", False, False),
    ]


def test_a_vocab_word_the_draft_left_unmarked_is_not_highlighted():
    assert _fragments("My sister is ten.", "sister") == [
        ("My", False, True),
        ("sister", False, True),
        ("is", False, True),
        ("ten.", False, True),
    ]


def test_post_text_falls_back_to_the_paragraph_when_no_caption_was_written():
    lesson = Lesson(
        topic="School", level=CEFRLevel.B1, paragraph="A short lesson.", caption="  "
    )

    assert lesson.post_text == "A short lesson."


def test_a_lesson_missing_its_paragraph_and_vocab_cannot_be_published():
    with pytest.raises(IncompleteLessonError, match="Paragraph and Vocabulary"):
        Lesson(topic="School", level=CEFRLevel.B1).ensure_publishable()
