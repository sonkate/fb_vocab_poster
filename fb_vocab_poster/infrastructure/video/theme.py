"""Every visual constant in one place, so restyling never means hunting through
drawing code."""
import os
from dataclasses import dataclass, field
from typing import Sequence, Tuple

from PIL import ImageFont

from .text import leading

RGB = Tuple[int, int, int]

SQUARE_HEIGHT = 1080   # 1:1, the original feed post
FEED_HEIGHT = 1350     # 4:5, Meta's recommended portrait feed size
REEL_HEIGHT = 1920     # 9:16, full-screen Reels

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
    "assets",
    "fonts",
)

BRAND_FONT_CANDIDATES: Sequence[str] = (
    os.path.join(ASSETS_DIR, "BeVietnamPro-Regular.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
)
BRAND_BOLD_FONT_CANDIDATES: Sequence[str] = (
    os.path.join(ASSETS_DIR, "BeVietnamPro-Bold.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
)

# Phonetic symbols (ˈ ʌ ŋ ʃ ə ː θ ð) are absent from most display faces, and a
# missing glyph renders as tofu rather than failing loudly. The IPA line is
# therefore pinned to its own family, so swapping the brand font above can
# never silently break pronunciation. tests/test_theme_fonts.py guards this.
IPA_FONT_CANDIDATES: Sequence[str] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    os.path.join(ASSETS_DIR, "BeVietnamPro-Regular.ttf"),
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


@dataclass(frozen=True)
class Theme:
    """The "Lên Band" palette and the canvas it is painted on.

    Width stays at 1080 whatever the height, so the type scale and margins
    below never need retuning — only vertical room changes. Pass
    `height=REEL_HEIGHT` for 9:16 Reels (what `container.py` builds),
    `FEED_HEIGHT` for a 4:5 feed post, or `SQUARE_HEIGHT` for the original
    square. Every layout below derives from these two numbers rather than
    hard-coding a canvas size.
    """

    width: int = 1080
    height: int = FEED_HEIGHT
    left: int = 70
    right: int = 70
    top: int = 90
    bottom: int = 70

    background: RGB = (27, 39, 51)     # #1B2733 — dark slate; makes the gold carry
    accent: RGB = (255, 193, 69)       # #FFC145 — brand gold; headings, IPA, taught words
    text: RGB = (232, 241, 248)        # #E8F1F8 — body copy
    muted: RGB = (106, 137, 167)       # #6A89A7 — rules and secondary detail
    danger: RGB = (255, 122, 107)      # #FF7A6B — the wrong half of a contrast slide

    # One colour per CEFR band, worn by the level chip. The chip is a filled
    # light shape, so its type is dark — brand text on mint is unreadable.
    level_a: RGB = (95, 211, 160)      # #5FD3A0 — mint
    level_b: RGB = (99, 179, 237)      # #63B3ED — sky
    level_c: RGB = (180, 139, 255)     # #B48BFF — violet
    level_text: RGB = (18, 32, 43)     # #12202B — type sitting on a level colour

    body_size: int = 40
    line_height: int = 56
    entry_gap: int = 16
    heading_size: int = 56
    word_size: int = 88
    ipa_size: int = 44
    meaning_size: int = 38

    # Contrast slides (mistake, upgrade) stack label / before / after / note.
    # Both halves are often whole sentences, so they sit well below word_size.
    label_size: int = 34
    contrast_from_size: int = 48
    contrast_to_size: int = 64

    # Fixed chrome: the wordmark top left, the level chip top right, the series
    # label along the foot. Every teaching slide wears all three in the same
    # place, which is the whole of the brand's recognisability in a feed.
    chrome_size: int = 38
    chrome_rule_gap: int = 12      # wordmark down to the gold rule under it
    chrome_rule_width: int = 96
    chrome_rule_height: int = 6
    chip_size: int = 32
    chip_padding_x: int = 28
    chip_padding_y: int = 12
    chip_radius: int = 20
    series_size: int = 28
    series_tracking: int = 6       # extra room between the foot label's letters
    chrome_gap: int = 70           # clear space between the chrome and the content

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

    # The wordmark is two-toned — the tail carries the accent colour, and that
    # single repeated detail is what makes the page recognisable in a feed.
    brand_lead: str = "LÊN"
    brand_tail: str = "BAND"
    tagline: str = "Mỗi ngày một bậc từ vựng."

    brand_fonts: Sequence[str] = field(default=BRAND_FONT_CANDIDATES)
    brand_bold_fonts: Sequence[str] = field(default=BRAND_BOLD_FONT_CANDIDATES)
    ipa_fonts: Sequence[str] = field(default=IPA_FONT_CANDIDATES)

    @property
    def max_width(self) -> int:
        return self.width - self.left - self.right

    @property
    def chrome_height(self) -> int:
        """Room the top chrome claims below `top`. The chip and the wordmark
        block are near enough the same height that either can be the taller."""
        mark = leading(self.chrome_size) + self.chrome_rule_gap + self.chrome_rule_height
        chip = leading(self.chip_size) + self.chip_padding_y * 2
        return max(mark, chip)

    @property
    def content_top(self) -> int:
        """Top edge of the band a slide may draw its own content in."""
        return self.top + self.chrome_height + self.chrome_gap

    @property
    def content_bottom(self) -> int:
        return self.height - self.bottom - leading(self.series_size) - self.chrome_gap

    @property
    def body_top(self) -> int:
        """Where body copy starts on a slide that has a heading."""
        return self.content_top + self.rule_offset + self.body_offset

    @property
    def content_height(self) -> int:
        return self.content_bottom - self.body_top

    @property
    def lines_per_page(self) -> int:
        return max(1, self.content_height // self.line_height)

    def font(self, size: int, bold: bool = False):
        """The brand face, for words, headings and Vietnamese copy."""
        return _first_available(
            self.brand_bold_fonts if bold else self.brand_fonts, size
        )

    def ipa_font(self, size: int):
        """The phonetic face. Never route non-IPA text through this."""
        return _first_available(self.ipa_fonts, size)

    def level_color(self, level) -> RGB:
        """Chip colour for a CEFR level, keyed by its band so A1 and A2 read
        as the same tier at a glance. Takes a `CEFRLevel` or its code."""
        band = str(level).strip().upper()[:1]
        return {"A": self.level_a, "B": self.level_b, "C": self.level_c}.get(
            band, self.muted
        )


def _first_available(candidates: Sequence[str], size: int):
    """First candidate that exists wins; the bundled default is the last
    resort so rendering never hard-fails on a bare machine."""
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()
