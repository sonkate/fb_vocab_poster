"""Turns painted slides plus the narration track into an MP4.

Implements `application.ports.VideoRenderer`. Slide durations come straight from
`domain.build_slide_plan`, so picture and sound cannot drift apart.
"""
from dataclasses import dataclass, field
from typing import List

from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

from ...application.ports import DraftRef, Narration, Workspace
from ...domain import Lesson, build_slide_plan
from .slide_painter import PillowSlidePainter
from .theme import Theme

FPS = 24


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
        plan = build_slide_plan(narration.segments, prepared.paragraph_page_weights)

        clips: List[ImageClip] = [
            ImageClip(prepared.paint(request, workdir, index)).set_duration(request.duration)
            for index, request in enumerate(plan)
        ]

        video = concatenate_videoclips(clips, method="compose")
        audio = AudioFileClip(narration.audio_path)
        video = video.set_audio(audio).set_fps(self.fps)
        try:
            video.write_videofile(
                out_path,
                codec="libx264",
                audio_codec="aac",
                verbose=False,
                logger=None,
            )
        finally:
            video.close()
            audio.close()
        return out_path
