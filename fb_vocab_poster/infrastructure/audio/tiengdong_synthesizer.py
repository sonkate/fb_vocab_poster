"""Text-to-speech via TiengDong's web TTS tool (https://tiengdong.com/text-to-speech).

Implements `application.ports.SpeechSynthesizer`. Same shape as
`GttsSpeechSynthesizer`/`TtsMakerSpeechSynthesizer` — one method, nothing
upstream knows which engine spoke.

TiengDong has no published API: this calls the same WordPress admin-ajax
endpoint their page's own "Convert" button calls
(`action=atts_convert`), authenticated with a `PHPSESSID` + `atts_user_id`
cookie pair captured from a real browser session. Like TTSMaker, converting
one cue is an order-then-fetch pair — the ajax call returns a JSON payload
with a download URL, not audio bytes directly.

This is unofficial and noticeably more fragile than gTTS/TTSMaker: the
captured `PHPSESSID` is a live session, not an API key, so it can go stale.
If `synthesize` starts raising `SynthesisError` with `MISSING_COOKIE_ID` or
similar, re-capture both values (open the TTS page, convert any text, find
the `admin-ajax.php` request in DevTools → Network, copy the `PHPSESSID` and
`atts_user_id` cookies) and update `.env`.
"""
import os
from dataclasses import dataclass

import requests

from ...domain import HOOK, SpeechCue

CONVERT_URL = "https://tiengdong.com/wp-admin/admin-ajax.php"
REQUEST_TIMEOUT_SECONDS = 60


class SynthesisError(RuntimeError):
    """TiengDong rejected the request, or the generated audio couldn't be fetched."""


@dataclass(frozen=True)
class TiengDongSpeechSynthesizer:
    php_session_id: str
    cookie_id: str
    voice: str = "en-US-Standard-E"
    # The hook slide's line is Vietnamese (see domain.narration.build_audio_plan)
    # — everything else spoken is the English being taught, so only the hook
    # switches voice.
    hook_voice: str = "vi-VN-Wavenet-C"
    speed: float = 1.0
    slow_speed: float = 0.7
    volume: float = 1.5
    pitch: float = 1.0
    timeout: int = REQUEST_TIMEOUT_SECONDS

    def _voice_for(self, cue: SpeechCue) -> str:
        return self.hook_voice if cue.kind == HOOK else self.voice

    def synthesize(self, cue: SpeechCue, out_path: str) -> str:
        if not self.php_session_id or not self.cookie_id:
            raise SynthesisError(
                "TIENGDONG_PHPSESSID / TIENGDONG_COOKIE_ID missing from .env"
            )

        order = requests.post(
            CONVERT_URL,
            data={
                "action": "atts_convert",
                "text": cue.text,
                "voice": self._voice_for(cue),
                "speed": self.slow_speed if cue.slow else self.speed,
                "volume": self.volume,
                "pitch": self.pitch,
                "enable-echo": "0",
                "background_music": "",
                "intro_music": "",
                "current-url": "110077",
                "site-language": "vi",
                "cookie_id": self.cookie_id,
                "cf-turnstile-response": "",
            },
            cookies={
                "PHPSESSID": self.php_session_id,
                "atts_user_id": self.cookie_id,
                "pll_language": "vi",
            },
            headers={
                "accept": "*/*",
                "origin": "https://tiengdong.com",
                "referer": "https://tiengdong.com/text-to-speech",
            },
            timeout=self.timeout,
        )
        try:
            payload = order.json()
        except ValueError:
            payload = {}
        if order.status_code != 200 or not payload.get("success"):
            raise SynthesisError(f"TiengDong TTS error: {payload or order.text}")

        audio_url = payload["data"]["atts_audio_url"]
        audio = requests.get(audio_url, timeout=self.timeout)
        if audio.status_code != 200:
            raise SynthesisError(
                f"TiengDong audio download failed: HTTP {audio.status_code}"
            )

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "wb") as handle:
            handle.write(audio.content)
        return out_path
