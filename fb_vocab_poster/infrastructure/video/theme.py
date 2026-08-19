"""Every visual constant in one place, so restyling never means hunting through
drawing code."""
import os
from dataclasses import dataclass, field
from typing import Sequence, Tuple

from PIL import ImageFont

RGB = Tuple[int, int, int]

REGULAR_FONT_CANDIDATES: Sequence[str] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
)
BOLD_FONT_CANDIDATES: Sequence[str] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)


@dataclass(frozen=True)
class Theme:
    """The "stormy morning" palette and the canvas it is painted on.

    1080x1350 is Meta's recommended 4:5 portrait size: it claims noticeably
    more of a phone screen than a square without leaving the feed's aspect
    ratio. Width stays at 1080, so the type scale and margins below are
    unchanged from the square layout — only vertical room grows.

    Pass `Theme(height=1080)` for the old square canvas, or
    `Theme(height=1920)` for a 9:16 reel; every layout below derives from
    these two numbers rather than hard-coding a canvas size.
    """

    width: int = 1080
    height: int = 1350
    left: int = 70
    right: int = 70
    top: int = 90
    bottom: int = 70

    background: RGB = (56, 73, 89)     # #384959 — dark blue-gray
    accent: RGB = (255, 193, 69)       # #FFC145 — warm gold; headings, IPA, taught words
    text: RGB = (189, 221, 252)        # #BDDDFC — body copy
    muted: RGB = (106, 137, 167)       # #6A89A7 — rules and secondary detail

    body_size: int = 40
    line_height: int = 56
    entry_gap: int = 16
    heading_size: int = 56
    word_size: int = 88
    ipa_size: int = 44
    meaning_size: int = 38

    rule_offset: int = 100     # distance from `top` down to the heading rule
    body_offset: int = 50      # distance from that rule down to body copy
    accent_bar_height: int = 14

    # Vertical gaps stacked down a word slide: word -> IPA -> rule -> meaning.
    # The slide centres the whole stack, so these describe its internal
    # spacing rather than any absolute position on the canvas.
    word_ipa_gap: int = 15
    ipa_rule_gap: int = 35
    rule_meaning_gap: int = 55
    meaning_inset: int = 100   # extra side margin so meanings wrap narrower
    rule_half_width: int = 120

    regular_fonts: Sequence[str] = field(default=REGULAR_FONT_CANDIDATES)
    bold_fonts: Sequence[str] = field(default=BOLD_FONT_CANDIDATES)

    @property
    def max_width(self) -> int:
        return self.width - self.left - self.right

    @property
    def body_top(self) -> int:
        """Where body copy starts on a slide that has a heading."""
        return self.top + self.rule_offset + self.body_offset

    @property
    def content_height(self) -> int:
        return self.height - self.body_top - self.bottom

    @property
    def lines_per_page(self) -> int:
        return max(1, self.content_height // self.line_height)

    def font(self, size: int, bold: bool = False):
        """First candidate that exists wins; the bundled default is the
        last resort so rendering never hard-fails on a bare machine."""
        for path in self.bold_fonts if bold else self.regular_fonts:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, size)
                except OSError:
                    continue
        return ImageFont.load_default()
