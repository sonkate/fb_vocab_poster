"""Renders the LÊN BAND identity assets from the palette in `theme.py`, so a
colour or wordmark change is repainted by rerunning this, never by hand.

    venv/bin/python scripts/build_brand_assets.py

The mark is BẬC: a three-tread staircase plus a detached cap — the rung not yet
climbed. Its geometry lives in a 100×100 unit box below and is the single source
both this script and `assets/brand/mark.svg` are drawn from.
"""
from __future__ import annotations

import os
import sys
from typing import Iterable, Sequence, Tuple

from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fb_vocab_poster.infrastructure.video.theme import Theme  # noqa: E402

RGB = Tuple[int, int, int]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "assets", "brand")

# One solid staircase in a 100×100 unit box: separated bars read as a signal
# icon, joined treads read as steps. Corners stay sharp, like the gold rule
# under the wordmark.
MARK_STAIR: Sequence[Tuple[int, int]] = (
    (12, 88), (12, 64), (38, 64), (38, 44), (64, 44), (64, 24), (90, 24), (90, 88),
)
MARK_CAP: Tuple[int, int, int, int] = (64, 4, 90, 16)  # the rung not yet climbed
INK_LEFT, INK_TOP, INK_RIGHT, INK_BOTTOM = 12, 4, 90, 88
INK_W = INK_RIGHT - INK_LEFT
INK_H = INK_BOTTOM - INK_TOP

# Facebook crops a square avatar to a circle, so the mark keeps a wide margin:
# 55% of the diameter leaves room for the story ring without clipping a step.
MARK_SHARE_OF_DIAMETER = 0.55

SUPERSAMPLE = 4  # rounded corners alias badly at final size


UNIT_CX = (INK_LEFT + INK_RIGHT) / 2
UNIT_CY = (INK_TOP + INK_BOTTOM) / 2


def draw_mark(draw: ImageDraw.ImageDraw, cx: float, cy: float, ink_height: float, color: RGB) -> None:
    scale = ink_height / INK_H
    place = lambda x, y: (cx + (x - UNIT_CX) * scale, cy + (y - UNIT_CY) * scale)
    draw.polygon([place(x, y) for x, y in MARK_STAIR], fill=color)
    x0, y0, x1, y1 = MARK_CAP
    draw.rectangle([*place(x0, y0), *place(x1, y1)], fill=color)


def canvas(width: int, height: int, background: RGB) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width * SUPERSAMPLE, height * SUPERSAMPLE), background)
    return image, ImageDraw.Draw(image)


def save(image: Image.Image, width: int, height: int, name: str) -> str:
    path = os.path.join(OUT_DIR, name)
    image.resize((width, height), Image.LANCZOS).save(path)
    return path


def tracked_text(
    draw: ImageDraw.ImageDraw, xy: Tuple[float, float], text: str, font, fill: RGB, tracking: float
) -> None:
    """Letter-spaced text — Pillow has no tracking, and the foot label and the
    cover's rhythm line both need it."""
    x, y = xy
    for char in text:
        draw.text((x, y), char, font=font, fill=fill)
        x += draw.textlength(char, font=font) + tracking


def wordmark(
    draw: ImageDraw.ImageDraw, xy: Tuple[float, float], theme: Theme, size: int
) -> Tuple[float, float]:
    """Draws `LÊN BAND` with the tail in accent. Returns the bottom-right corner."""
    font = theme.font(size, bold=True)
    x, y = xy
    lead = f"{theme.brand_lead} "
    draw.text((x, y), lead, font=font, fill=theme.text)
    x += draw.textlength(lead, font=font)
    draw.text((x, y), theme.brand_tail, font=font, fill=theme.accent)
    x += draw.textlength(theme.brand_tail, font=font)
    return x, y + font.getbbox("Hg")[3]


def build_avatar(theme: Theme, size: int, name: str, *, inverted: bool) -> str:
    ground = theme.accent if inverted else theme.background
    ink = theme.background if inverted else theme.accent
    image, draw = canvas(size, size, ground)
    unit = size * SUPERSAMPLE
    draw_mark(draw, unit / 2, unit / 2, unit * MARK_SHARE_OF_DIAMETER, ink)
    return save(image, size, size, name)


def build_cover(theme: Theme) -> str:
    width, height = 1640, 624
    image, draw = canvas(width, height, theme.background)
    s = SUPERSAMPLE

    draw.rectangle([0, 0, width * s, 10 * s], fill=theme.accent)

    # Everything readable stays inside the 640×312 centre: that is all the
    # mobile crop keeps, and the profile picture covers the lower left.
    x = 540 * s
    y = 214 * s
    _, mark_bottom = wordmark(draw, (x, y), theme, 84 * s)
    rule_y = mark_bottom + 26 * s
    draw.rectangle([x, rule_y, x + 150 * s, rule_y + 10 * s], fill=theme.accent)

    tagline_font = theme.font(34 * s)
    tagline_y = rule_y + 34 * s
    draw.text((x, tagline_y), theme.tagline, font=tagline_font, fill=theme.text)

    rhythm_font = theme.font(22 * s)
    tracked_text(
        draw,
        (x, tagline_y + 66 * s),
        "5 TỪ MỖI NGÀY · T2 - T6 · A1 - C1",
        rhythm_font,
        theme.muted,
        6 * s,
    )

    # Steps climbing off the right edge: decoration the mobile crop may eat
    # without losing a word. Three bars, matching the mark's three treads.
    base = 486 * s
    bar_w, gap = 42 * s, 16 * s
    right = (width - 96) * s
    heights = (90, 175, 260)
    left = right - (len(heights) * bar_w + (len(heights) - 1) * gap)
    for index, bar_height in enumerate(heights):
        bar_x = left + index * (bar_w + gap)
        draw.rounded_rectangle(
            [bar_x, base - bar_height * s, bar_x + bar_w, base], radius=7 * s, fill=theme.accent
        )
    tallest_x = left + (len(heights) - 1) * (bar_w + gap)
    cap_bottom = base - (heights[-1] + 30) * s
    draw.rounded_rectangle(
        [tallest_x, cap_bottom - 30 * s, tallest_x + bar_w, cap_bottom], radius=7 * s, fill=theme.accent
    )

    return save(image, width, height, "cover.png")


def build_lockup(theme: Theme) -> str:
    width, height = 1200, 320
    image, draw = canvas(width, height, theme.background)
    s = SUPERSAMPLE
    draw_mark(draw, 190 * s, height / 2 * s, 168 * s, theme.accent)
    right, bottom = wordmark(draw, (330 * s, 96 * s), theme, 96 * s)
    draw.rectangle([330 * s, bottom + 18 * s, right, bottom + 28 * s], fill=theme.accent)
    return save(image, width, height, "lockup.png")


def rgb_hex(color: RGB) -> str:
    return "#{:02X}{:02X}{:02X}".format(*color)


def build_mark_svg(theme: Theme) -> Iterable[str]:
    """Two SVGs: the bare mark (currentColor, for any surface) and the avatar
    exactly as uploaded — solid accent disc, mark knocked out in the ground."""
    points = " ".join(f"{x},{y}" for x, y in MARK_STAIR)
    cx0, cy0, cx1, cy1 = MARK_CAP
    cap = f'<rect x="{cx0}" y="{cy0}" width="{cx1 - cx0}" height="{cy1 - cy0}"/>'
    mark = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
        'width="100" height="100" role="img" aria-label="Lên Band">\n'
        f'  <g fill="currentColor">\n    <polygon points="{points}"/>\n    {cap}\n  </g>\n</svg>\n'
    )

    scale = MARK_SHARE_OF_DIAMETER * 100 / INK_H
    tx = 50 - UNIT_CX * scale
    ty = 50 - UNIT_CY * scale
    avatar = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" '
        'width="100" height="100" role="img" aria-label="Lên Band">\n'
        f'  <rect width="100" height="100" fill="{rgb_hex(theme.accent)}"/>\n'
        f'  <g transform="translate({tx:.3f} {ty:.3f}) scale({scale:.4f})" '
        f'fill="{rgb_hex(theme.background)}">\n'
        f'    <polygon points="{points}"/>\n    {cap}\n  </g>\n</svg>\n'
    )

    written = []
    for name, body in (("mark.svg", mark), ("avatar.svg", avatar)):
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        written.append(path)
    return written


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    theme = Theme()

    written = [
        *build_mark_svg(theme),
        build_avatar(theme, 1080, "avatar.png", inverted=True),
        build_avatar(theme, 1080, "avatar-dark.png", inverted=False),
        build_avatar(theme, 512, "favicon.png", inverted=True),
        build_cover(theme),
        build_lockup(theme),
    ]
    for path in written:
        print(os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
