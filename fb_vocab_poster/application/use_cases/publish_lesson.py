"""Use case: render a draft and post the result to a page."""
from dataclasses import dataclass
from typing import Tuple

from ..ports import LessonPublisher, ProgressReporter, PublishReceipt, RenderedLesson
from .render_lesson import RenderLesson


@dataclass(frozen=True)
class PublishLesson:
    render: RenderLesson
    publisher: LessonPublisher
    reporter: ProgressReporter

    def __call__(self, identifier: str) -> Tuple[RenderedLesson, PublishReceipt]:
        rendered = self.render(identifier)
        self.reporter.step("Posting to Facebook Page...")
        receipt = self.publisher.publish(
            rendered.video_path, rendered.lesson.post_text
        )
        return rendered, receipt
