"""Use case: read an edited draft and render the narrated video from it.

This is the whole `build` command, and the first half of `publish`.
"""
from dataclasses import dataclass

from ..ports import (
    DraftRepository,
    NarrationComposer,
    ProgressReporter,
    RenderedLesson,
    VideoRenderer,
)


@dataclass(frozen=True)
class RenderLesson:
    repository: DraftRepository
    narrator: NarrationComposer
    video_renderer: VideoRenderer
    reporter: ProgressReporter

    def __call__(self, identifier: str) -> RenderedLesson:
        ref = self.repository.reference(identifier)
        lesson = self.repository.load(identifier)
        lesson.ensure_publishable()

        self.reporter.step(
            "Generating narration (each word spoken slow, then normal, then the paragraph)..."
        )
        narration = self.narrator.compose(lesson, ref)

        self.reporter.step("Rendering video slides...")
        video_path = self.video_renderer.render(lesson, narration, ref)

        return RenderedLesson(lesson=lesson, narration=narration, video_path=video_path)
