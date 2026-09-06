"""The fixed chrome is what makes a slide recognisable mid-scroll, so its
three marks are asserted on real pixels rather than trusted to survive the
next layout change."""
from fb_vocab_poster.domain import CEFRLevel, Lesson, VocabEntry, OUTRO, WORD
from fb_vocab_poster.infrastructure.video import PillowSlidePainter, Theme, REEL_HEIGHT

THEME = Theme(height=REEL_HEIGHT)


def prepared(level: CEFRLevel = CEFRLevel.A1):
    lesson = Lesson(
        topic="Family",
        level=level,
        vocab=(VocabEntry("mother", "/ˈmʌðər/", "a woman who has a child"),),
        paragraph="My mother is a teacher.",
    )
    return PillowSlidePainter(theme=THEME).prepare(lesson)


def slide(kind: str, level: CEFRLevel = CEFRLevel.A1):
    prep = prepared(level)
    return prep._word(prep.lesson.vocab[0]) if kind == WORD else prep._outro()


def _rows_with_content(image):
    background = THEME.background
    return [
        y
        for y in range(image.height)
        if any(image.getpixel((x, y)) != background for x in range(0, image.width, 4))
    ]


def test_the_chip_wears_the_colour_of_the_lesson_level():
    for level in CEFRLevel:
        image = slide(WORD, level)
        chip = image.getpixel((THEME.width - THEME.right - 40, THEME.top + 30))

        assert chip == THEME.level_color(level)


def test_the_wordmark_sits_in_the_top_left_corner_of_every_teaching_slide():
    image = slide(WORD)
    strip = [
        image.getpixel((x, THEME.top + 20))
        for x in range(THEME.left, THEME.left + 200)
    ]

    assert THEME.accent in strip and THEME.text in strip


def test_the_series_label_anchors_the_foot():
    image = slide(WORD)
    foot = _rows_with_content(image)[-1]

    assert THEME.content_bottom < foot < THEME.height - THEME.bottom


def test_content_is_centred_in_the_band_the_frame_leaves():
    """The complaint the frame exists to fix: a short stack floating in a tall
    canvas. Whatever a slide draws should sit centred between the chrome."""
    image = slide(WORD)
    rows = [y for y in _rows_with_content(image) if THEME.content_top < y < THEME.content_bottom]

    above = rows[0] - THEME.content_top
    below = THEME.content_bottom - rows[-1]
    assert abs(above - below) < THEME.line_height


def test_the_outro_wears_no_chrome_of_its_own():
    """It is the wordmark, full size and centred — a corner copy would be the
    same mark twice."""
    image = slide(OUTRO)
    corner = [
        image.getpixel((x, y))
        for y in range(THEME.top, THEME.top + 60)
        for x in range(THEME.left, THEME.left + 260, 4)
    ]

    assert set(corner) == {THEME.background}
