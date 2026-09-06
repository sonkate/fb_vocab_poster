import pytest

from fb_vocab_poster.domain import CEFRLevel, InvalidLessonFile, Lesson, VocabEntry
from fb_vocab_poster.infrastructure.content import markdown_format

DRAFT = """---
topic: Ordering coffee
level: b1
---

## Vocabulary
- barista — /bəˈriːstə/ — a person who makes coffee
- roast — /roʊst/ — how long beans are cooked

## Paragraph
The **barista** asked about the **roast** I wanted.

## Caption
Level: B1 — tell us your order! #english #vocab
"""


def test_parses_frontmatter_sections_and_vocab_rows():
    lesson = markdown_format.parse(DRAFT)

    assert lesson.topic == "Ordering coffee"
    assert lesson.level is CEFRLevel.B1
    assert [entry.word for entry in lesson.vocab] == ["barista", "roast"]
    assert lesson.vocab[0].ipa == "/bəˈriːstə/"
    assert lesson.vocab[0].meaning == "a person who makes coffee"


def test_bold_markers_survive_parsing_because_they_say_what_is_taught():
    assert markdown_format.parse(DRAFT).paragraph == (
        "The **barista** asked about the **roast** I wanted."
    )


def test_the_spoken_and_posted_paragraph_has_no_markers_in_it():
    assert markdown_format.parse(DRAFT).plain_paragraph == (
        "The barista asked about the roast I wanted."
    )


def test_a_draft_without_a_level_says_so_instead_of_guessing():
    with pytest.raises(InvalidLessonFile, match="level"):
        markdown_format.parse("## Paragraph\nno frontmatter here", source="draft.md")


def test_render_round_trips_back_through_parse():
    lesson = Lesson(
        topic="Travel",
        level=CEFRLevel.A2,
        vocab=(VocabEntry(word="platform", ipa="/ˈplætfɔːm/", meaning="where trains stop"),),
        paragraph="Wait on the platform.",
        caption="Level: A2 #travel",
    )

    assert markdown_format.parse(markdown_format.render(lesson)) == lesson
