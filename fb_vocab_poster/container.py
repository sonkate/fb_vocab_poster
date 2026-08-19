"""Composition root: the one place that knows which adapter fills which port.

Every dependency is wired here and injected downwards, so a use case can be
exercised in a test with fakes and no wiring code has to be duplicated.
"""
from dataclasses import dataclass
from functools import cached_property

from .application import DraftLesson, PublishLesson, RenderLesson
from .application.ports import LessonDrafter
from .infrastructure.audio import MoviePyNarrationComposer, TtsMakerSpeechSynthesizer
from .infrastructure.config import FileSystemWorkspace, Settings, SystemClock
from .infrastructure.content import (
    AnthropicDrafter,
    MarkdownDraftRepository,
    TemplateDrafter,
)
from .infrastructure.publishing import FacebookPagePublisher
from .infrastructure.video import MoviePyVideoRenderer, PillowSlidePainter, Theme
from .interface.console import ConsoleReporter


@dataclass
class Container:
    settings: Settings

    @classmethod
    def from_env(cls) -> "Container":
        return cls(settings=Settings.from_env())

    # -- shared collaborators --------------------------------------------

    @cached_property
    def reporter(self) -> ConsoleReporter:
        return ConsoleReporter()

    @cached_property
    def clock(self) -> SystemClock:
        return SystemClock()

    @cached_property
    def workspace(self) -> FileSystemWorkspace:
        return FileSystemWorkspace(output_dir=self.settings.output_dir)

    @cached_property
    def repository(self) -> MarkdownDraftRepository:
        return MarkdownDraftRepository(drafts_dir=self.settings.drafts_dir)

    @cached_property
    def theme(self) -> Theme:
        return Theme()

    @cached_property
    def drafter(self) -> LessonDrafter:
        """With a key, Claude writes the draft; without one, we lay out a blank
        template of the same shape for the user to paste into."""
        if self.settings.can_auto_draft:
            return AnthropicDrafter(
                api_key=self.settings.anthropic_api_key,
                model=self.settings.anthropic_model,
            )
        return TemplateDrafter()

    @cached_property
    def narrator(self) -> MoviePyNarrationComposer:
        return MoviePyNarrationComposer(
            synthesizer=TtsMakerSpeechSynthesizer(api_key=self.settings.ttsmaker_api_key),
            workspace=self.workspace,
        )

    @cached_property
    def video_renderer(self) -> MoviePyVideoRenderer:
        return MoviePyVideoRenderer(
            painter=PillowSlidePainter(theme=self.theme),
            workspace=self.workspace,
            theme=self.theme,
        )

    @cached_property
    def publisher(self) -> FacebookPagePublisher:
        return FacebookPagePublisher(
            page_id=self.settings.facebook_page_id,
            access_token=self.settings.facebook_page_access_token,
            graph_version=self.settings.facebook_graph_version,
        )

    # -- use cases --------------------------------------------------------

    @cached_property
    def draft_lesson(self) -> DraftLesson:
        return DraftLesson(
            drafter=self.drafter, repository=self.repository, clock=self.clock
        )

    @cached_property
    def render_lesson(self) -> RenderLesson:
        return RenderLesson(
            repository=self.repository,
            narrator=self.narrator,
            video_renderer=self.video_renderer,
            reporter=self.reporter,
        )

    @cached_property
    def publish_lesson(self) -> PublishLesson:
        return PublishLesson(
            render=self.render_lesson,
            publisher=self.publisher,
            reporter=self.reporter,
        )
