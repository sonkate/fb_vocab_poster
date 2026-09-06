import pytest

from fb_vocab_poster.domain import (
    CEFRLevel,
    FORMATS,
    IncompleteLessonError,
    InvalidLessonFile,
    Lesson,
    LessonFormat,
    VocabEntry,
    build_audio_plan,
)
from fb_vocab_poster.infrastructure.content import markdown_format

MISTAKE_DRAFT = """---
topic: Common slips
level: a2
format: mistake
---

## Mistakes
- I very like it. — I really like it. — "very" cannot modify a verb
- I have 25 years old. — I am 25. — age takes "to be"

## Caption
How would you fix the first one?
"""


def mistake_lesson() -> Lesson:
    return Lesson(
        topic="Common slips",
        level=CEFRLevel.A2,
        format=LessonFormat.MISTAKE,
        vocab=(VocabEntry("I very like it.", "I really like it.", "no verb modifier"),),
    )


def test_a_draft_without_a_format_is_the_vocabulary_format():
    """Drafts written before formats existed carry no `format:` line."""
    lesson = markdown_format.parse(
        "---\ntopic: T\nlevel: b1\n---\n\n## Vocabulary\n- a — b — c\n"
    )

    assert lesson.format is LessonFormat.VOCAB


def test_an_unknown_format_names_the_ones_that_exist():
    with pytest.raises(InvalidLessonFile, match="vocab"):
        LessonFormat.parse("carousel")


def test_each_format_reads_its_rows_from_its_own_section():
    lesson = markdown_format.parse(MISTAKE_DRAFT)

    assert lesson.format is LessonFormat.MISTAKE
    assert lesson.spec.section == "Mistakes"
    assert [entry.columns[0] for entry in lesson.vocab] == [
        "I very like it.",
        "I have 25 years old.",
    ]


def test_a_contrast_format_narrates_the_correction_once_and_has_no_paragraph():
    """A vocabulary word is worth hearing slowly then at speed; a corrected
    sentence only needs saying once, and there is no paragraph to read."""
    plan = build_audio_plan(mistake_lesson())

    assert [cue.text for cue in plan] == ["I really like it."]
    assert [cue.slow for cue in plan] == [False]


def test_a_format_without_a_paragraph_is_publishable_without_one():
    mistake_lesson().ensure_publishable()


def test_a_missing_section_is_named_by_the_format_that_wanted_it():
    empty = Lesson(topic="T", level=CEFRLevel.A2, format=LessonFormat.UPGRADE)

    with pytest.raises(IncompleteLessonError, match="Upgrades"):
        empty.ensure_publishable()


def test_render_round_trips_every_format():
    for lesson_format in LessonFormat:
        lesson = Lesson(
            topic="T",
            level=CEFRLevel.B1,
            format=lesson_format,
            vocab=(VocabEntry("one", "two", "three"),),
            paragraph="A paragraph." if lesson_format is LessonFormat.VOCAB else "",
            caption="A caption.",
        )

        assert markdown_format.parse(markdown_format.render(lesson)) == lesson


def test_every_format_names_its_own_series():
    assert all(spec.series_label for spec in FORMATS.values())
    assert len({spec.series_label for spec in FORMATS.values()}) == len(FORMATS)


def test_the_series_caption_carries_the_topic_of_the_episode():
    spec = FORMATS[LessonFormat.VOCAB]

    assert spec.series_caption("Job Interviews") == "5 từ mỗi ngày · job interviews"


def test_a_lesson_without_a_topic_shows_the_series_alone():
    spec = FORMATS[LessonFormat.MISTAKE]

    assert spec.series_caption("") == "Sai chỗ nào"
    assert spec.series_caption("   ") == "Sai chỗ nào"
