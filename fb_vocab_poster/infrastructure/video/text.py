"""Text measurement and wrapping helpers, shared by every slide layout."""
from typing import Iterable, List, Sequence

from ...domain.lesson import Fragment


def wrap_plain(draw, text: str, font, max_width: int) -> List[str]:
    """Greedy word wrap into lines no wider than `max_width`."""
    lines: List[str] = []
    current: List[str] = []
    for word in text.split():
        trial = " ".join(current + [word])
        if current and draw.textlength(trial, font=font) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines or [""]


def wrap_tokens(
    draw, fragments: Iterable[Fragment], font, max_width: int
) -> List[List[Fragment]]:
    """Same wrap, but over `Fragment`s so the taught words keep their flag
    through to drawing. A line only ever breaks where a word begins, which is
    what keeps a trailing full stop with the word it belongs to."""
    space = draw.textlength(" ", font=font)
    lines: List[List[Fragment]] = []
    current: List[Fragment] = []
    current_width = 0.0

    for fragment in fragments:
        width = draw.textlength(fragment.text, font=font)
        gap = space if current and fragment.starts_word else 0.0
        if current and fragment.starts_word and current_width + gap + width > max_width:
            lines.append(current)
            current, current_width, gap = [], 0.0, 0.0
        current.append(fragment)
        current_width += gap + width

    if current:
        lines.append(current)
    return lines or [[]]


def paginate(lines: Sequence, per_page: int) -> List[List]:
    """Splits wrapped lines into screenfuls, spread as evenly as possible.

    Filling every page to `per_page` before starting the next can strand a
    handful of lines alone on a final page — a page as tall as the rest but
    holding a fifth of the text reads as empty even once its narration time
    is weighted correctly. Balancing page sizes keeps every page similarly
    full instead.
    """
    if not lines:
        return [[]]
    pages = max(1, -(-len(lines) // per_page))  # ceil division
    base, extra = divmod(len(lines), pages)
    result: List[List] = []
    start = 0
    for page in range(pages):
        size = base + (1 if page < extra else 0)
        result.append(list(lines[start:start + size]))
        start += size
    return result


def draw_token_line(
    draw, fragments: Sequence[Fragment], x: int, y: float, font, highlight_font, color, highlight_color
) -> None:
    space = draw.textlength(" ", font=font)
    for index, fragment in enumerate(fragments):
        f = highlight_font if fragment.highlighted else font
        if index and fragment.starts_word:
            x += space
        draw.text(
            (x, y),
            fragment.text,
            font=f,
            fill=highlight_color if fragment.highlighted else color,
        )
        x += draw.textlength(fragment.text, font=f)


def leading(size: int) -> int:
    """Leading scales with the type size, so this reads correctly for both body
    copy and large display type. Takes a size rather than a font, so a layout
    can reserve room before it has loaded one."""
    return int(size * 1.3)


def line_height(font) -> int:
    return leading(font.size)


def block_height(lines: Sequence, font) -> int:
    """Total height a set of wrapped lines will occupy once drawn."""
    return len(lines) * line_height(font)


def draw_centered(draw, lines: Sequence[str], font, top: float, color, canvas_width: int) -> float:
    """Draws horizontally-centred lines from a fixed top edge, returning the y
    just past the last one."""
    leading = line_height(font)
    y = top
    for line in lines:
        width = draw.textlength(line, font=font)
        draw.text(((canvas_width - width) / 2, y), line, font=font, fill=color)
        y += leading
    return y


def draw_tracked(draw, text: str, font, y: float, color, canvas_width: int, tracking: int) -> None:
    """Centred small caps with letters held apart — the foot label is tiny, and
    tracking is what keeps it legible rather than a smudge."""
    widths = [draw.textlength(char, font=font) for char in text]
    x = (canvas_width - (sum(widths) + tracking * max(0, len(text) - 1))) / 2
    for char, width in zip(text, widths):
        draw.text((x, y), char, font=font, fill=color)
        x += width + tracking
