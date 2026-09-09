"""Which sound plays after each half of a contrast-rhythm row is a name the
domain declares (`FormatSpec.contrast_from/to_stinger`) and the composer
looks up — this is that lookup, tested without touching TTS or disk."""
import subprocess

import imageio_ffmpeg
import pytest

from fb_vocab_poster.infrastructure.audio.moviepy_composer import MoviePyNarrationComposer, _voice_span


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


def test_voice_span_trims_silence_padded_onto_either_end_of_a_clip(tmp_path):
    """A synthesized stand-in for a TTS clip: 0.3s of silence, a 1.0s tone,
    then 0.4s of silence — the same shape as the padding a real TTS engine
    puts around the words it actually says. `_voice_span` must report the
    tone's own span, not the file's full 1.7s."""
    path = str(tmp_path / "probe.mp3")
    result = subprocess.run(
        [
            imageio_ffmpeg.get_ffmpeg_exe(), "-y",
            "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-f", "lavfi", "-i", "sine=f=440:r=22050",
            "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-filter_complex",
            "[0]atrim=0:0.3[a];[1]atrim=0:1.0[b];[2]atrim=0:0.4[c];[a][b][c]concat=n=3:v=0:a=1[out]",
            "-map", "[out]", path,
        ],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr

    voice_start, voice_end = _voice_span(path, duration=1.7)

    assert voice_start == pytest.approx(0.3, abs=0.05)
    assert voice_end == pytest.approx(1.3, abs=0.05)
