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


def test_the_upgrade_transition_is_shorter_than_either_mistake_stinger():
    """The transition is synthesized, not a recorded asset, and isn't meant
    to carry a verdict — it should read as brief, not as a stinger."""
    composer = _composer()
    timing = composer.timing
    transition = composer._stinger("transition", [])

    assert transition.duration == timing.transition_duration
    assert transition.duration < timing.buzzer_duration
    assert transition.duration < timing.ding_duration


def test_a_blank_stinger_name_means_no_sound_at_all():
    assert _composer()._stinger("", []) is None


def test_the_default_timing_gives_upgrade_no_second_stinger():
    """`upgrade`'s FormatSpec leaves `contrast_to_stinger` blank — nothing
    plays before the reading pause, unlike `mistake`'s ding."""
    from fb_vocab_poster.domain import FORMATS, LessonFormat

    spec = FORMATS[LessonFormat.UPGRADE]

    assert spec.contrast_from_stinger == "transition"
    assert spec.contrast_to_stinger == ""
