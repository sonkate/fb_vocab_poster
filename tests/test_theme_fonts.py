"""Guards the one thing a brand-font swap can silently break.

A font without a phonetic glyph does not fail — it draws tofu, and the mistake
only shows up in a finished video. So the IPA family is asserted here, on every
test run, rather than trusted.
"""
from PIL import ImageFont

from fb_vocab_poster.infrastructure.video.theme import Theme

IPA_GLYPHS = "ˈʌŋʃəːθðɜɒæɪʊʒ"
VIETNAMESE_GLYPHS = "ăâđêôơưạỹễệ"

# Codepoints no Latin face carries. Whatever the font draws for these *is* its
# "missing glyph" shape, which is what makes the comparison below font-agnostic:
# some faces draw an empty box, others draw nothing at all.
ABSENT = "漢"
ALSO_ABSENT = "🙂"


def _signature(font: ImageFont.FreeTypeFont, char: str):
    mask = font.getmask(char)
    return mask.size, bytes(mask)


def _missing(font: ImageFont.FreeTypeFont, text: str):
    notdef = _signature(font, ABSENT)
    return [char for char in text if _signature(font, char) == notdef]


def test_the_detector_actually_detects_a_missing_glyph():
    assert _missing(Theme().ipa_font(48), ALSO_ABSENT) == [ALSO_ABSENT]


def test_ipa_font_covers_every_phonetic_symbol_used_on_a_word_slide():
    assert _missing(Theme().ipa_font(48), IPA_GLYPHS) == []


def test_brand_font_covers_vietnamese_diacritics():
    theme = Theme()
    assert _missing(theme.font(48), VIETNAMESE_GLYPHS) == []
    assert _missing(theme.font(48, bold=True), VIETNAMESE_GLYPHS) == []
