"""Turns painted slides plus the narration track into an MP4.

Implements `application.ports.VideoRenderer`. Slide durations come straight from
`domain.build_slide_plan`, so picture and sound cannot drift apart.
"""
import os
from dataclasses import dataclass, field
from typing import List

import numpy as np
from moviepy.editor import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    VideoClip,
    concatenate_videoclips,
)
from moviepy.video.fx.fadein import fadein

from ...application.ports import DraftRef, Narration, Workspace
from ...domain import Lesson, build_slide_plan
from .slide_painter import PillowSlidePainter
from .theme import Theme

FPS = 24

# Every slide fades in rather than hard-cutting — a static frame reads as a
# photo and gets scrolled past; a fade is the cheapest possible pattern
# interrupt that says "this is playing". Capped per-slide below so a very
# short one (e.g. the mistake format's "wrong" stage) is never held at less
# than half-visible for most of its own duration.
SLIDE_FADE_IN = 0.35


@dataclass(frozen=True)
class MoviePyVideoRenderer:
    painter: PillowSlidePainter
    workspace: Workspace
    fps: int = FPS
    theme: Theme = field(default_factory=Theme)

    def render(self, lesson: Lesson, narration: Narration, ref: DraftRef) -> str:
        workdir = self.workspace.slides_workdir(ref.basename)
        out_path = self.workspace.video(ref.basename)

        prepared = self.painter.prepare(lesson)
        plan = build_slide_plan(narration.segments, prepared.paragraph_page_weights, lesson.hook_line)

        clips: List[ImageClip] = []
        for index, request in enumerate(plan):
            clip = ImageClip(prepared.paint(request, workdir, index)).set_duration(request.duration)
            if request.fade_in:
                clip = fadein(clip, min(SLIDE_FADE_IN, request.duration / 2))
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")
        video = CompositeVideoClip([video, self._progress_bar(video.duration)])
        audio = AudioFileClip(narration.audio_path)
        video = video.set_audio(audio).set_fps(self.fps)
        # Encode to a sibling temp path and rename into place only once it's
        # whole: `write_videofile` isn't atomic, so a render that dies partway
        # (an interrupted process, an upstream TTS failure further up the
        # call stack on a *different* run) used to leave a truncated,
        # unplayable MP4 sitting at `out_path` — clobbering whatever finished
        # video a viewer already had open there.
        tmp_path = f"{out_path}.tmp"
        try:
            video.write_videofile(
                tmp_path,
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None,
            )
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise
        finally:
            video.close()
            audio.close()
        os.replace(tmp_path, out_path)
        return out_path

    def _progress_bar(self, duration: float) -> VideoClip:
        """A bar along the bottom edge that fills over the video's whole
        runtime — the one element guaranteed to keep moving even through a
        long silent reading pause, which is what actually satisfies "sống
        được khi tắt tiếng" rather than just decorating individual slides."""
        theme = self.theme
        height = theme.progress_bar_height
        track = np.array(theme.progress_track, dtype=np.uint8)
        fill = np.array(theme.accent, dtype=np.uint8)

        def make_frame(t):
            frame = np.tile(track, (height, theme.width, 1))
            filled = int(theme.width * min(t / duration, 1.0))
            if filled:
                frame[:, :filled] = fill
            return frame

        bar = VideoClip(make_frame, duration=duration)
        return bar.set_position((0, theme.height - height))
