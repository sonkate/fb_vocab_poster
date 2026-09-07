"""Stitches synthesised speech into one narration track with moviepy.

Implements `application.ports.NarrationComposer`. What gets spoken is decided by
`domain.build_audio_plan`; this class only performs it and measures the result,
because real durations are the one thing the domain cannot know in advance.
"""
import os
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np
from moviepy.audio.AudioClip import AudioClip
from moviepy.editor import AudioFileClip, concatenate_audioclips

from ...application.ports import DraftRef, Narration, SpeechSynthesizer, Workspace
from ...domain import (
    OUTRO,
    PARAGRAPH,
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


def _tone(freq: float, duration: float, fps: int = FPS) -> AudioClip:
    """A short sine note, faded in and out so it doesn't click. Returned
    stereo (mono duplicated to both channels) — a bare mono frame breaks
    moviepy's `CompositeAudioClip` mixing, which assumes every child clip's
    frame already carries a channel axis."""

    def make_frame(t):
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        envelope = np.sin(np.pi * np.clip(t_arr, 0, duration) / duration) ** 0.5
        mono = 0.28 * np.sin(2 * np.pi * freq * t_arr) * envelope
        stereo = np.column_stack([mono, mono])
        return stereo if np.ndim(t) else stereo[0]

    return AudioClip(make_frame, duration=duration, fps=fps)


def _buzzer(duration: float, fps: int = FPS) -> AudioClip:
    """The "sai" cue. No licensed SFX file — a falling pitch turned into a
    square wave gives it the rasp of a real buzzer without needing one."""

    def make_frame(t):
        t_arr = np.atleast_1d(np.asarray(t, dtype=float))
        f0, f1 = 220.0, 90.0
        phase = 2 * np.pi * (f0 * t_arr + (f1 - f0) * t_arr**2 / (2 * duration))
        envelope = np.sin(np.pi * np.clip(t_arr, 0, duration) / duration) ** 0.5
        mono = 0.25 * np.sign(np.sin(phase)) * envelope
        stereo = np.column_stack([mono, mono])
        return stereo if np.ndim(t) else stereo[0]

    return AudioClip(make_frame, duration=duration, fps=fps)


def _ding(duration: float, fps: int = FPS) -> AudioClip:
    """The "đúng" cue: two short, bright notes rising a fifth — a chime
    shape, distinct from the buzzer's single falling tone."""
    half = duration / 2
    return concatenate_audioclips([_tone(880.0, half, fps), _tone(1318.5, half, fps)])


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

        spec = lesson.spec
        if spec.contrast_rhythm:
            row_clips, row_segments = self._contrast_track(lesson, speech)
            clips.extend(row_clips)
            segments.extend(row_segments)
        else:
            for index, entry in enumerate(lesson.vocab):
                fast = speech[f"word_{index}_normal"]
                if spec.repeat_slowly:
                    slow = speech[f"word_{index}_slow"]
                    clips.extend([slow, _silence(self.timing.pause_between_slow_fast)])
                    duration = word_segment_duration(
                        slow.duration, fast.duration, self.timing
                    )
                else:
                    duration = fast.duration + self.timing.pause_after_word
                clips.extend([fast, _silence(self.timing.pause_after_word)])
                segments.append(
                    NarrationSegment(
                        kind=spec.slide_kind, duration=duration, vocab=entry
                    )
                )

        if spec.needs_paragraph:
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

    def _contrast_track(
        self, lesson: Lesson, speech: Dict[str, AudioFileClip]
    ) -> Tuple[List, List[NarrationSegment]]:
        """The "spot the mistake" rhythm: wrong sentence, buzz — its own slide,
        so the fix can't be read off-screen while it plays — then right
        sentence, ding, and a hold long enough to read the Vietnamese
        explanation before the next row starts."""
        spec = lesson.spec
        clips: List = []
        segments: List[NarrationSegment] = []

        for index, entry in enumerate(lesson.vocab):
            wrong = speech[f"{spec.slide_kind}_{index}_wrong"]
            right = speech[f"{spec.slide_kind}_{index}_right"]
            buzzer = _buzzer(self.timing.buzzer_duration)
            ding = _ding(self.timing.ding_duration)
            note_words = len(entry.columns[2].split())
            reading_pause = (
                self.timing.reading_pause_base
                + self.timing.reading_seconds_per_word * note_words
            )

            clips.extend([wrong, buzzer])
            segments.append(
                NarrationSegment(
                    kind=spec.slide_kind,
                    duration=wrong.duration + buzzer.duration,
                    vocab=entry,
                    stage="wrong",
                )
            )

            clips.extend([right, ding, _silence(reading_pause)])
            segments.append(
                NarrationSegment(
                    kind=spec.slide_kind,
                    duration=right.duration + ding.duration + reading_pause,
                    vocab=entry,
                    stage="full",
                )
            )

        return clips, segments

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
