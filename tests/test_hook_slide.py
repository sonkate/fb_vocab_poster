"""The opening hook slide: no chrome (that's the whole point — nothing should
compete with the claim), and text big enough to actually be there."""
from PIL import ImageDraw

from fb_vocab_poster.domain import CEFRLevel, Lesson
from fb_vocab_poster.infrastructure.video import PillowSlidePainter, REEL_HEIGHT, Theme

THEME = Theme(height=REEL_HEIGHT)


def _prepared(hook: str = "") -> "PreparedSlides":
    lesson = Lesson(topic="Family", level=CEFRLevel.A1, hook=hook)
    return PillowSlidePainter(theme=THEME).prepare(lesson)


def _count_color(image, color, stride=2):
    return sum(
        1
        for y in range(0, image.height, stride)
        for x in range(0, image.width, stride)
        if image.getpixel((x, y)) == color
    )


def test_the_hook_slide_wears_no_chrome():
    """A teaching slide always has a gold strip along the very top edge (see
    `_frame`); the hook skips `_frame` entirely, so that strip must be gone."""
    image = _prepared("5 lỗi ai cũng mắc")._hook()
    top_strip = [
        image.getpixel((x, y))
        for y in range(0, THEME.accent_bar_height)
        for x in range(0, THEME.width, 8)
    ]

    assert all(pixel == THEME.background for pixel in top_strip)


def test_the_hook_slide_draws_large_accent_text():
    image = _prepared("5 lỗi ai cũng mắc")._hook()

    assert _count_color(image, THEME.accent) > 0


def test_a_blank_hook_still_renders_the_formats_default_line():
    """A draft that never set `hook:` must still open on something rather
    than a blank card."""
    image = _prepared("")._hook()

    assert _count_color(image, THEME.accent) > 0


def test_a_real_hook_line_shrinks_to_keep_within_three_lines():
    """A real 6-7 word Vietnamese hook is wide at `hook_size` — this is the
    actual regression that motivated `hook_size_min`: it used to floor out
    one step short and land these exact lines on 4 rows."""
    prepared = _prepared()
    probe, draw = prepared._canvas()
    font, lines = prepared._fit_hook_font(draw, "Nói tiếng Anh nghe như người bản xứ")

    assert len(lines) <= 3
    assert font.size < THEME.hook_size
