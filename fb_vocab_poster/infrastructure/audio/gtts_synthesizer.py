"""Free text-to-speech via gTTS (Google Translate).

Implements `application.ports.SpeechSynthesizer`. Swapping in ElevenLabs or
Azure Neural TTS means writing another class with this one method — nothing
upstream knows which engine spoke.
"""
import os
from dataclasses import dataclass

from gtts import gTTS

from ...domain import SpeechCue


@dataclass(frozen=True)
class GttsSpeechSynthesizer:
    lang: str = "en"

    def synthesize(self, cue: SpeechCue, out_path: str) -> str:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        gTTS(text=cue.text, lang=self.lang, slow=cue.slow).save(out_path)
        return out_path
