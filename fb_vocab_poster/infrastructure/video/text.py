"""Text measurement and wrapping helpers, shared by every slide layout."""
from typing import Iterable, List, Optional, Sequence

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


def _line_width(draw, line: Sequence[Fragment], font, highlight_font) -> float:
    space = draw.textlength(" ", font=font)
    width = 0.0
    for index, fragment in enumerate(line):
        f = highlight_font if fragment.highlighted else font
        if index and fragment.starts_word:
            width += space
        width += draw.textlength(fragment.text, font=f)
    return width


def draw_centered_tokens(
    draw,
    lines: Sequence[Sequence[Fragment]],
    font,
    top: float,
    color,
    canvas_width: int,
    highlight_font=None,
    highlight_color=None,
    underline: bool = False,
) -> float:
    """Centres wrapped fragment lines, setting a highlighted fragment apart
    either by weight (pass `highlight_font`, the taught-word convention) or by
    an underline in the same weight (`underline=True`). A mistake slide needs
    the latter for its wrong span — bolding it would read as emphasis, the
    same treatment the correct answer gets, when the point is the opposite."""
    highlight_font = highlight_font or font
    highlight_color = highlight_color if highlight_color is not None else color
    space = draw.textlength(" ", font=font)
    leading = line_height(font)
    y = top
    for line in lines:
        x = (canvas_width - _line_width(draw, line, font, highlight_font)) / 2
        for index, fragment in enumerate(line):
            f = highlight_font if fragment.highlighted else font
            if index and fragment.starts_word:
                x += space
            fill = highlight_color if fragment.highlighted else color
            draw.text((x, y), fragment.text, font=f, fill=fill)
            width = draw.textlength(fragment.text, font=f)
            if fragment.highlighted and underline:
                under_y = y + f.size + 4
                draw.line(
                    [(x, under_y), (x + width, under_y)],
                    fill=highlight_color,
                    width=max(2, f.size // 18),
                )
            x += width
        y += leading
    return y


def draw_centered_reveal(
    draw,
    lines: Sequence[Sequence[Fragment]],
    font,
    top: float,
    color,
    canvas_width: int,
    visible_through: int,
    highlight_index: Optional[int],
    pill_color,
    pill_text_color,
    pill_padding_x: float,
    pill_padding_y: float,
    pill_radius: float,
) -> float:
    """A word-by-word reveal caption: only fragments up to the
    `visible_through`-th word (counting across every line) are drawn at
    all — a word not reached yet is skipped rather than dimmed, so nothing
    leaks ahead of the narration — and the `highlight_index`-th word sits on
    a filled, rounded pill in `pill_color` with its own text flipped to
    `pill_text_color` so it stays legible on the fill. Each line re-centres
    on whichever of its own words are visible so far, so a line grows from
    the middle outward exactly like the reveal it's showing; only `top`
    (sized from the caller's full, final wrap) holds still across every
    state of one reveal, so the block doesn't jump vertically as it fills."""
    leading = line_height(font)
    y = top
    index = 0
    for line in lines:
        visible = list(line[: max(0, visible_through - index + 1)])
        width = _line_width(draw, visible, font, font)
        x = (canvas_width - width) / 2

        cursor = x
        for local_i, fragment in enumerate(visible):
            if local_i and fragment.starts_word:
                cursor += draw.textlength(" ", font=font)
            w = draw.textlength(fragment.text, font=font)
            if index + local_i == highlight_index:
                draw.rounded_rectangle(
                    [
                        (cursor - pill_padding_x, y - pill_padding_y),
                        (cursor + w + pill_padding_x, y + font.size + pill_padding_y),
                    ],
                    radius=pill_radius,
                    fill=pill_color,
                )
            cursor += w

        cursor = x
        for local_i, fragment in enumerate(visible):
            if local_i and fragment.starts_word:
                cursor += draw.textlength(" ", font=font)
            fill = pill_text_color if index + local_i == highlight_index else color
            draw.text((cursor, y), fragment.text, font=font, fill=fill)
            cursor += draw.textlength(fragment.text, font=font)

        index += len(line)
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
