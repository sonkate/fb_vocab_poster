from fb_vocab_poster.domain import HOOK, WORD, SpeechCue
from fb_vocab_poster.infrastructure.audio.tiengdong_synthesizer import (
    TiengDongSpeechSynthesizer,
)


def _synth(**overrides) -> TiengDongSpeechSynthesizer:
    return TiengDongSpeechSynthesizer(php_session_id="s", cookie_id="c", **overrides)


def test_the_hook_cue_speaks_in_the_vietnamese_voice():
    """The hook line is the one thing spoken in Vietnamese — everything else
    is the English being taught, so only this cue's voice differs."""
    synth = _synth()

    assert synth._voice_for(SpeechCue(kind=HOOK, text="Xin chào")) == synth.hook_voice


def test_every_other_cue_keeps_the_configured_english_voice():
    synth = _synth()

    assert synth._voice_for(SpeechCue(kind=WORD, text="hello")) == synth.voice


def test_the_vietnamese_voice_defaults_to_wavenet_c():
    assert _synth().hook_voice == "vi-VN-Wavenet-C"
