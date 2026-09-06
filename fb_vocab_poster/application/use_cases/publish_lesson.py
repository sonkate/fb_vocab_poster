"""Use case: render a draft and post the result to a page — or, with
`skip_render`, post whatever this draft already rendered instead of paying
for TTS and video rendering again.
"""
from dataclasses import dataclass
from typing import Tuple

from ...domain import StaleRenderError
from ..ports import (
    DraftRepository,
    LessonPublisher,
    Narration,
    ProgressReporter,
    PublishReceipt,
    RenderedLesson,
    Workspace,
)
from .render_lesson import RenderLesson


@dataclass(frozen=True)
class PublishLesson:
    render: RenderLesson
    repository: DraftRepository
    workspace: Workspace
    publisher: LessonPublisher
    reporter: ProgressReporter

    def __call__(
        self, identifier: str, *, skip_render: bool = False
    ) -> Tuple[RenderedLesson, PublishReceipt]:
        rendered = (
            self._reuse_existing_render(identifier)
            if skip_render
            else self.render(identifier)
        )
        self.reporter.step("Posting to Facebook Page...")
        receipt = self.publisher.publish(
            rendered.video_path, rendered.lesson.post_text
        )
        return rendered, receipt

    def _reuse_existing_render(self, identifier: str) -> RenderedLesson:
        ref = self.repository.reference(identifier)
        lesson = self.repository.load(identifier)
        lesson.ensure_publishable()

        since = self.repository.modified_at(identifier)
        video_path = self.workspace.fresh_video(ref.basename, since=since)
        if video_path is None:
            raise StaleRenderError(
                f"No video for '{ref.basename}' is newer than the draft — "
                f"run `build {identifier}` first, or drop --skip-render."
            )

        self.reporter.step(f"Reusing already-rendered video: {video_path}")
        narration = Narration(
            audio_path=self.workspace.narration_audio(ref.basename), segments=()
        )
        return RenderedLesson(lesson=lesson, narration=narration, video_path=video_path)
