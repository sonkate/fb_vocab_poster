"""Every visual constant in one place, so restyling never means hunting through
drawing code."""
import os
from dataclasses import dataclass, field
from typing import Sequence, Tuple

from PIL import ImageFont

from .text import leading

RGB = Tuple[int, int, int]

SQUARE_HEIGHT = 1080   # 1:1, the original feed post
FEED_HEIGHT = 1350     # 4:5, Meta's recommended portrait feed size — the
                        # baseline every size in _SCALED_FIELDS is tuned at
REEL_HEIGHT = 1920     # 9:16, full-screen Reels

# Content type sizes and internal gaps, scaled by Theme.__post_init__ so a
# taller canvas fills with bigger content instead of the same stack floating
# in more empty space. Everything else — brand chrome (wordmark, chip,
# footer) and canvas margins — stays a fixed pixel size on any height, since
# that fixed size is what makes it recognisable across formats.
_SCALED_FIELDS: Sequence[str] = (
    "body_size", "line_height", "entry_gap", "heading_size",
    "word_size", "word_size_min", "ipa_size", "meaning_size",
    "contrast_from_size", "contrast_to_size",
    "rule_offset", "body_offset", "accent_bar_height",
    "word_ipa_gap", "ipa_rule_gap", "rule_meaning_gap",
    "meaning_inset", "rule_half_width", "rule_thickness",
    "outro_mark_size", "outro_detail_size", "outro_cta_size", "outro_cta_gap",
    "badge_size", "badge_padding_x", "badge_padding_y", "badge_radius", "badge_gap",
    "hook_size", "hook_size_min",
)

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

    Width stays at 1080 whatever the height. `container.py` currently builds
    at `REEL_HEIGHT` (9:16); this field defaults to `FEED_HEIGHT` (4:5) as
    the size every type/gap value below is tuned against — `__post_init__`
    scales them for any other height, so a taller canvas fills with bigger
    content instead of the same stack floating in more empty space. Fixed
    brand chrome (wordmark, chip, footer, margins) is exempt: see
    `_SCALED_FIELDS`.
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
    muted: RGB = (106, 137, 167)       # #6A89A7 — rules and the IPA line
    text_soft: RGB = (169, 189, 205)   # #A9BDCD — a meaning, read after the word
    danger: RGB = (255, 122, 107)      # #FF7A6B — the wrong half of a contrast slide

    # One colour per CEFR band, worn by the level chip. The chip is a filled
    # light shape, so its type is dark — brand text on mint is unreadable.
    level_a: RGB = (95, 211, 160)      # #5FD3A0 — mint
    level_b: RGB = (99, 179, 237)      # #63B3ED — sky
    level_c: RGB = (180, 139, 255)     # #B48BFF — violet
    level_text: RGB = (18, 32, 43)     # #12202B — type sitting on a level colour

    body_size: int = 52
    line_height: int = 74
    entry_gap: int = 16
    heading_size: int = 68

    # The taught word is the hero of its slide and is set to fill the frame.
    # `word_size` is therefore a ceiling, not a fixed size: a long word steps
    # down towards `word_size_min` rather than wrapping onto a second line,
    # which reads far worse than a slightly smaller word.
    word_size: int = 170
    word_size_min: int = 96
    ipa_size: int = 68
    meaning_size: int = 56

    # Contrast slides (mistake, upgrade) stack before / after / note. Both
    # halves are often whole sentences, so they sit well below word_size.
    contrast_from_size: int = 60
    contrast_to_size: int = 80

    # Fixed chrome: the wordmark top left, the level chip top right, the series
    # label along the foot. Every teaching slide wears all three in the same
    # place, which is the whole of the brand's recognisability in a feed.
    chrome_size: int = 44
    chrome_rule_gap: int = 12      # wordmark down to the gold rule under it
    chrome_rule_width: int = 94
    chrome_rule_height: int = 11
    chip_size: int = 40
    chip_padding_x: int = 28
    chip_padding_y: int = 12
    chip_radius: int = 20
    series_size: int = 35
    series_tracking: int = 3       # extra room between the foot label's letters
    chrome_gap: int = 70           # clear space between the chrome and the content

    rule_offset: int = 116     # distance from `top` down to the heading rule
    body_offset: int = 50      # distance from that rule down to body copy
    accent_bar_height: int = 14

    # Vertical gaps stacked down a word slide: word -> IPA -> rule -> meaning.
    # The slide centres the whole stack, so these describe its internal
    # spacing rather than any absolute position on the canvas.
    word_ipa_gap: int = 28
    ipa_rule_gap: int = 48
    rule_meaning_gap: int = 60
    meaning_inset: int = 100   # extra side margin so meanings wrap narrower
    rule_half_width: int = 94
    rule_thickness: int = 6

    # The outro borrows the word slide's gaps but pins its own type sizes: it
    # is the only slide where the mark is the content, so it must not grow
    # with the hero word or the read-along copy.
    outro_mark_size: int = 88
    outro_detail_size: int = 40

    # The call-to-action sits below the tagline/topic block, set apart by its
    # own gap so it reads as a separate prompt rather than another detail line.
    outro_cta_size: int = 46
    outro_cta_gap: int = 56
    outro_cta: str = "Theo dõi để tiến bộ mỗi ngày"

    # The "SAI" tag on a mistake slide's wrong-only half — same pill shape as
    # the level chip, but centred rather than pinned to a corner.
    badge_size: int = 40
    badge_padding_x: int = 26
    badge_padding_y: int = 10
    badge_radius: int = 18
    badge_gap: int = 36

    # The opening hook slide wears no chrome, so it's the one slide free to
    # go bigger than `word_size` — it has the whole canvas to itself and
    # needs to read at thumbnail scale before a scroll carries it past.
    # `hook_size_min` sits low enough that a real 6-7 word Vietnamese hook
    # (the `default_hook` strings in lesson_format.py) can still shrink into
    # `_fit_hook_font`'s 3-line cap — at 110 it floored out one step short
    # and those exact strings landed on 4 lines instead.
    hook_size: int = 200
    hook_size_min: int = 90

    # The wordmark is two-toned — the tail carries the accent colour, and that
    # single repeated detail is what makes the page recognisable in a feed.
    brand_lead: str = "LÊN"
    brand_tail: str = "BAND"
    tagline: str = "Mỗi ngày một bậc từ vựng."

    brand_fonts: Sequence[str] = field(default=BRAND_FONT_CANDIDATES)
    brand_bold_fonts: Sequence[str] = field(default=BRAND_BOLD_FONT_CANDIDATES)
    ipa_fonts: Sequence[str] = field(default=IPA_FONT_CANDIDATES)

    def __post_init__(self) -> None:
        scale = self.height / FEED_HEIGHT
        if scale == 1.0:
            return
        for name in _SCALED_FIELDS:
            object.__setattr__(self, name, round(getattr(self, name) * scale))

    @property
    def accent_soft(self) -> RGB:
        """Accent at half strength. Pillow draws onto an RGB canvas with no
        alpha, and blending against a known background is the same result as
        compositing without needing a second layer for one rule."""
        return tuple(
            (channel + ground) // 2
            for channel, ground in zip(self.accent, self.background)
        )

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
