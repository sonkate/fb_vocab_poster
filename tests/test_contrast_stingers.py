"""Which sound plays after each half of a contrast-rhythm row is a name the
domain declares (`FormatSpec.contrast_from/to_stinger`) and the composer
looks up — this is that lookup, tested without touching TTS or disk."""
from fb_vocab_poster.infrastructure.audio.moviepy_composer import MoviePyNarrationComposer


def _composer() -> MoviePyNarrationComposer:
    return MoviePyNarrationComposer(synthesizer=None, workspace=None)


def test_buzz_and_ding_run_the_full_recorded_stinger_length():
    composer = _composer()
    timing = composer.timing

    assert composer._stinger("buzz", []).duration == timing.buzzer_duration
    assert composer._stinger("ding", []).duration == timing.ding_duration


def test_a_blank_stinger_name_means_no_sound_at_all():
    assert _composer()._stinger("", []) is None


def test_upgrade_shares_the_exact_same_stingers_as_mistake():
    """The user chose one consistent audio signature across formats over
    distinguishing "weak" from "wrong" — so `upgrade` reuses `mistake`'s
    buzz/ding instead of a format-specific sound."""
    from fb_vocab_poster.domain import FORMATS, LessonFormat

    mistake = FORMATS[LessonFormat.MISTAKE]
    upgrade = FORMATS[LessonFormat.UPGRADE]

    assert upgrade.contrast_from_stinger == mistake.contrast_from_stinger == "buzz"
    assert upgrade.contrast_to_stinger == mistake.contrast_to_stinger == "ding"
