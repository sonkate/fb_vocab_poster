"""Stitches synthesised speech into one narration track with moviepy.

Implements `application.ports.NarrationComposer`. What gets spoken is decided by
`domain.build_audio_plan`; this class only performs it and measures the result,
because real durations are the one thing the domain cannot know in advance.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List

from moviepy.audio.AudioClip import AudioClip
from moviepy.editor import AudioFileClip, concatenate_audioclips

from ...application.ports import DraftRef, Narration, SpeechSynthesizer, Workspace
from ...domain import (
    OUTRO,
    PARAGRAPH,
    WORD,
    Lesson,
    NarrationSegment,
    NarrationTiming,
    SpeechCue,
    build_audio_plan,
    word_segment_duration,
)

FPS = 44100


def _silence(duration: float, fps: int = FPS) -> AudioClip:
    return AudioClip(lambda t: 0, duration=duration, fps=fps)


@dataclass(frozen=True)
class MoviePyNarrationComposer:
    synthesizer: SpeechSynthesizer
    workspace: Workspace
    timing: NarrationTiming = field(default_factory=NarrationTiming)

    def compose(self, lesson: Lesson, ref: DraftRef) -> Narration:
        workdir = self.workspace.narration_workdir(ref.basename)
        out_path = self.workspace.narration_audio(ref.basename)

        speech = self._speak(build_audio_plan(lesson), workdir)
        clips: List = []
        segments: List[NarrationSegment] = []

        for index, entry in enumerate(lesson.vocab):
            slow = speech[f"word_{index}_slow"]
            fast = speech[f"word_{index}_normal"]
            clips.extend(
                [
                    slow,
                    _silence(self.timing.pause_between_slow_fast),
                    fast,
                    _silence(self.timing.pause_after_word),
                ]
            )
            segments.append(
                NarrationSegment(
                    kind=WORD,
                    duration=word_segment_duration(
                        slow.duration, fast.duration, self.timing
                    ),
                    vocab=entry,
                )
            )

        paragraph = speech[PARAGRAPH]
        clips.append(paragraph)
        segments.append(
            NarrationSegment(kind=PARAGRAPH, duration=paragraph.duration)
        )

        # The brand card closes in silence, after the lesson has earned it.
        clips.append(_silence(self.timing.outro_pause))
        segments.append(
            NarrationSegment(kind=OUTRO, duration=self.timing.outro_pause)
        )

        track = concatenate_audioclips(clips)
        try:
            track.write_audiofile(out_path, fps=FPS, verbose=False, logger=None)
        finally:
            track.close()
            for clip in speech.values():
                clip.close()

        return Narration(audio_path=out_path, segments=tuple(segments))

    def _speak(self, plan: List[SpeechCue], workdir: str) -> Dict[str, AudioFileClip]:
        """Renders every cue to disk and opens it, keyed by the cue's stable
        clip name so assembly can look pieces up without re-deriving paths."""
        clips: Dict[str, AudioFileClip] = {}
        for cue in plan:
            path = self.synthesizer.synthesize(
                cue, os.path.join(workdir, f"{cue.clip_name}.mp3")
            )
            clips[cue.clip_name] = AudioFileClip(path)
        return clips
