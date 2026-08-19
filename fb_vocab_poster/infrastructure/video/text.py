"""Text measurement and wrapping helpers, shared by every slide layout."""
from typing import Iterable, List, Sequence, Tuple

Token = Tuple[str, bool]


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


def wrap_tokens(draw, tokens: Iterable[Token], font, max_width: int) -> List[List[Token]]:
    """Same wrap, but over `(word, is_highlighted)` pairs so the taught words
    keep their flag through to drawing."""
    space = draw.textlength(" ", font=font)
    lines: List[List[Token]] = []
    current: List[Token] = []
    current_width = 0.0

    for word, highlighted in tokens:
        word_width = draw.textlength(word, font=font)
        advance = word_width if not current else word_width + space
        if current and current_width + advance > max_width:
            lines.append(current)
            current, current_width = [], 0.0
            advance = word_width
        current.append((word, highlighted))
        current_width += advance

    if current:
        lines.append(current)
    return lines or [[]]


def paginate(lines: Sequence, per_page: int) -> List[List]:
    """Splits wrapped lines into screenfuls."""
    if not lines:
        return [[]]
    return [list(lines[i:i + per_page]) for i in range(0, len(lines), per_page)]


def draw_token_line(
    draw, tokens: Sequence[Token], x: int, y: float, font, highlight_font, color, highlight_color
) -> None:
    space = draw.textlength(" ", font=font)
    for word, highlighted in tokens:
        f = highlight_font if highlighted else font
        draw.text((x, y), word, font=f, fill=highlight_color if highlighted else color)
        x += draw.textlength(word, font=f) + space


def line_height(font) -> int:
    """Leading scales with the font's own size, so this reads correctly for
    both body copy and large display type."""
    return int(font.size * 1.3)


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
