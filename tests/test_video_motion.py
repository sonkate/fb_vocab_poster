"""The progress bar is what actually guarantees Việc 3 (no dead air for a
muted viewer): it moves every frame regardless of what a slide is doing, so
it is worth testing on its own rather than only through a full render."""
from fb_vocab_poster.infrastructure.video.moviepy_renderer import MoviePyVideoRenderer
from fb_vocab_poster.infrastructure.video.theme import Theme


def _renderer(theme: Theme) -> MoviePyVideoRenderer:
    return MoviePyVideoRenderer(painter=None, workspace=None, theme=theme)


def _filled_width(frame, fill):
    fill = tuple(fill)
    width = 0
    for x in range(frame.shape[1]):
        if tuple(frame[0, x]) != fill:
            break
        width += 1
    return width


def test_the_bar_starts_empty_and_ends_full():
    theme = Theme()
    bar = _renderer(theme)._progress_bar(duration=10.0)

    assert _filled_width(bar.get_frame(0.0), theme.accent) == 0
    assert _filled_width(bar.get_frame(10.0), theme.accent) == theme.width


def test_the_bar_fills_monotonically():
    theme = Theme()
    bar = _renderer(theme)._progress_bar(duration=10.0)

    widths = [_filled_width(bar.get_frame(t), theme.accent) for t in (0, 2.5, 5, 7.5, 10)]

    assert widths == sorted(widths)
    assert widths[0] < widths[-1]


def test_the_bar_sits_flush_with_the_bottom_edge():
    theme = Theme()
    bar = _renderer(theme)._progress_bar(duration=10.0)

    x, y = bar.pos(0)
    assert (x, y) == (0, theme.height - theme.progress_bar_height)
