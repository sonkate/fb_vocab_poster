"""The mistake format's two-slide "spot the error" rhythm: pixel checks guard
the visual contract (SAI badge, red underline, gold pick-out, and the
no-markup fallback) the way test_slide_frame.py guards the shared chrome."""
from fb_vocab_poster.domain import CEFRLevel, Lesson, LessonFormat, VocabEntry
from fb_vocab_poster.infrastructure.video import PillowSlidePainter, REEL_HEIGHT, Theme

THEME = Theme(height=REEL_HEIGHT)

# One row marks its wrong/right word with `**`, the other doesn't — every
# test compares the two to prove the markup actually changes what's drawn,
# and that a row without it still falls back to the old full-sentence colour.
MARKED = VocabEntry("I **very** like it.", "I **really** like it.", "very can't modify a verb")
UNMARKED = VocabEntry("I have 25 years old.", "I am 25 years old.", "age takes to be")


def _count_color(image, color, stride=2):
    return sum(
        1
        for y in range(0, image.height, stride)
        for x in range(0, image.width, stride)
        if image.getpixel((x, y)) == color
    )


def _prepared(entry: VocabEntry, lesson_format: LessonFormat = LessonFormat.MISTAKE):
    lesson = Lesson(topic="Common slips", level=CEFRLevel.B1, format=lesson_format, vocab=(entry,))
    return PillowSlidePainter(theme=THEME).prepare(lesson)


def test_the_wrong_slide_wears_a_sai_badge():
    image = _prepared(MARKED)._contrast_wrong(MARKED)

    assert _count_color(image, THEME.danger) > 0


def test_a_marked_wrong_sentence_underlines_only_the_flagged_word():
    """Unmarked falls back to painting the whole sentence danger; marked only
    paints its one flagged word danger and leaves the rest in body text
    colour — so marked must show *less* danger and *more* plain text."""
    marked = _prepared(MARKED)._contrast_wrong(MARKED)
    unmarked = _prepared(UNMARKED)._contrast_wrong(UNMARKED)

    assert _count_color(unmarked, THEME.danger) > _count_color(marked, THEME.danger)
    assert _count_color(marked, THEME.text) > _count_color(unmarked, THEME.text)


def test_the_reveal_slide_picks_out_only_the_corrected_word_in_gold():
    marked = _prepared(MARKED)._contrast_reveal(MARKED)
    unmarked = _prepared(UNMARKED)._contrast_reveal(UNMARKED)

    assert _count_color(unmarked, THEME.accent) > _count_color(marked, THEME.accent)
    assert _count_color(marked, THEME.text) > _count_color(unmarked, THEME.text)


def test_upgrades_reveal_slide_still_renders_through_the_same_contrast_layout():
    """`upgrade` now runs the same two-slide before/after rhythm as `mistake`
    (Slide A: `_upgrade_weak`, below), but its reveal slide is still drawn by
    the original, unmodified `_contrast` layout."""
    entry = VocabEntry("very tired", "exhausted", "Band 5 -> 7.5, same idea")
    image = _prepared(entry, LessonFormat.UPGRADE)._contrast(entry)

    assert _count_color(image, THEME.accent) > 0
    assert _count_color(image, THEME.danger) > 0


def test_the_weak_slide_wears_a_neutral_badge_not_a_danger_one():
    """A weak phrase isn't wrong, so its own slide (Slide A) must not use
    the mistake rhythm's danger-red badge — only the neutral chip colour."""
    entry = VocabEntry("very tired", "exhausted", "Band 5 -> 7.5, same idea")
    image = _prepared(entry, LessonFormat.UPGRADE)._upgrade_weak(entry)

    assert _count_color(image, THEME.muted) > 0
    assert _count_color(image, THEME.danger) == 0
