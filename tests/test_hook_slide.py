"""The opening hook slide: no chrome (that's the whole point — nothing should
compete with the claim), text big enough to actually be there, and — since
the word-by-word reveal — only as much of the sentence as has been "read" so
far, with the current word boxed."""
from PIL import ImageDraw

from fb_vocab_poster.domain import CEFRLevel, Fragment, Lesson
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


def test_a_real_hook_line_shrinks_to_keep_within_two_lines():
    """A real 6-7 word Vietnamese hook is wide at `hook_size` — shrinking
    must still land it within the two-line cap the user asked for, with
    real margin either side rather than just under `max_width`."""
    prepared = _prepared()
    probe, draw = prepared._canvas()
    fragments = [Fragment(word) for word in "Nói tiếng Anh nghe như người bản xứ".split()]
    font, lines = prepared._fit_hook_font(draw, fragments)

    assert len(lines) <= 2
    assert font.size < THEME.hook_size
    for line in lines:
        width = max(draw.textlength(f.text, font=font) for f in line)
        assert width < THEME.width - 2 * THEME.left


def test_the_reveal_only_draws_words_up_to_the_highlighted_one():
    """`highlight_index=0` is the very first frame of the reveal: only the
    first word exists yet, the rest of the sentence hasn't "appeared"."""
    full = _prepared("5 lỗi ai cũng mắc")._hook(-1)
    first_word_only = _prepared("5 lỗi ai cũng mắc")._hook(0)

    assert _count_color(first_word_only, THEME.accent) < _count_color(full, THEME.accent)


def test_the_highlighted_word_sits_on_an_accent_pill_with_flipped_text():
    """The word currently being read gets a filled pill behind it, with its
    own text flipped to `level_text` so it reads against the fill — the
    plain, not-yet-highlighted words stay accent-on-background as before."""
    image = _prepared("5 lỗi ai cũng mắc")._hook(0)

    assert _count_color(image, THEME.level_text) > 0


def test_the_last_word_reveals_the_whole_sentence():
    hook = "5 lỗi ai cũng mắc"
    last_index = len(hook.split()) - 1

    last_word = _prepared(hook)._hook(last_index)
    full = _prepared(hook)._hook(-1)

    # Every word is visible by the last frame — same ink overall as the
    # full, unhighlighted line, just with the last word boxed instead.
    assert _count_color(last_word, THEME.accent) + _count_color(last_word, THEME.level_text) >= (
        _count_color(full, THEME.accent)
    )
