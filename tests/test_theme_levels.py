"""The level chip is the only place the palette varies by lesson, so the
band → colour map is asserted rather than eyeballed on a rendered slide."""
from fb_vocab_poster.domain import CEFRLevel
from fb_vocab_poster.infrastructure.video.theme import Theme

MINT = (95, 211, 160)
SKY = (99, 179, 237)
VIOLET = (180, 139, 255)


def test_every_level_wears_its_band_colour():
    theme = Theme()

    assert [theme.level_color(level) for level in CEFRLevel] == [
        MINT, MINT, SKY, SKY, VIOLET, VIOLET,
    ]


def test_a_level_code_works_as_well_as_the_enum():
    theme = Theme()

    assert theme.level_color("b2") == theme.level_color(CEFRLevel.B2)


def test_chip_type_is_dark_enough_to_read_on_every_band_colour():
    """Brand text on mint disappears; the chip therefore carries its own
    dark ink, and that has to stay darker than any band behind it."""
    theme = Theme()

    for level in CEFRLevel:
        assert sum(theme.level_text) < sum(theme.level_color(level))
