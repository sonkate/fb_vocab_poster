"""Text-to-speech via the TTSMaker HTTP API (https://ttsmaker.com).

Implements `application.ports.SpeechSynthesizer`. Same shape as
`GttsSpeechSynthesizer` — one method, nothing upstream knows which engine
spoke. TTSMaker's `create-tts-order` call doesn't return audio bytes, only a
temporary download URL, so synthesizing one cue is an order-then-fetch pair.
"""
import os
from dataclasses import dataclass

import requests

from ...domain import SpeechCue

CREATE_ORDER_URL = "https://api.ttsmaker.com/v2/create-tts-order"
REQUEST_TIMEOUT_SECONDS = 60


class SynthesisError(RuntimeError):
    """TTSMaker rejected the order, or the generated audio couldn't be fetched."""


@dataclass(frozen=True)
class TtsMakerSpeechSynthesizer:
    api_key: str
    voice_id: int = 778  # English (US)
    audio_format: str = "mp3"
    speed: float = 1.0
    slow_speed: float = 0.7
    timeout: int = REQUEST_TIMEOUT_SECONDS

    def synthesize(self, cue: SpeechCue, out_path: str) -> str:
        if not self.api_key:
            raise SynthesisError("TTSMAKER_API_KEY missing from .env")

        order = requests.post(
            CREATE_ORDER_URL,
            json={
                "api_key": self.api_key,
                "text": cue.text,
                "voice_id": self.voice_id,
                "audio_format": self.audio_format,
                "audio_speed": self.slow_speed if cue.slow else self.speed,
            },
            headers={"accept": "application/json"},
            timeout=self.timeout,
        )
        payload = order.json()
        if order.status_code != 200 or payload.get("error_code") != 0:
            raise SynthesisError(f"TTSMaker API error: {payload}")

        audio = requests.get(payload["audio_download_url"], timeout=self.timeout)
        if audio.status_code != 200:
            raise SynthesisError(
                f"TTSMaker audio download failed: HTTP {audio.status_code}"
            )

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "wb") as handle:
            handle.write(audio.content)
        return out_path
