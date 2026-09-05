"""Draws lesson slides with Pillow — no ImageMagick anywhere in the pipeline.

The painter answers two questions for the renderer: how many pages the
paragraph needs (which the domain needs before it can allocate screen time),
and what each requested slide looks like as a PNG.
"""
import os
from dataclasses import dataclass
from typing import List, Sequence

from PIL import Image, ImageDraw

from ...domain import PARAGRAPH, TITLE, WORD, Lesson, SlideRequest, VocabEntry
from . import text as text_utils
from .theme import Theme

TITLE_HEADING = "New words inside — listen and learn!"
PARAGRAPH_HEADING = "READ ALONG"


@dataclass(frozen=True)
class PreparedSlides:
    """A lesson laid out and ready to paint. Wrapping the paragraph is the
    expensive part, so it happens once here rather than per slide."""

    theme: Theme
    lesson: Lesson
    paragraph_pages: Sequence[Sequence[Sequence[text_utils.Token]]]

    @property
    def paragraph_page_count(self) -> int:
        return len(self.paragraph_pages)

    def paint(self, request: SlideRequest, workdir: str, index: int) -> str:
        if request.kind == TITLE:
            image = self._title()
        elif request.kind == WORD:
            image = self._word(request.vocab)
        elif request.kind == PARAGRAPH:
            image = self._paragraph(self.paragraph_pages[request.page])
        else:
            raise ValueError(f"Unknown slide kind: {request.kind!r}")

        os.makedirs(workdir, exist_ok=True)
        path = os.path.join(workdir, f"slide_{index:03d}_{request.kind}.png")
        image.save(path)
        return path

    # -- layouts ----------------------------------------------------------

    def _canvas(self):
        theme = self.theme
        image = Image.new("RGB", (theme.width, theme.height), theme.background)
        return image, ImageDraw.Draw(image)

    def _heading(self, draw, title: str) -> int:
        """Draws a left-aligned heading with a rule under it, returning the y
        where body copy starts."""
        theme = self.theme
        draw.text(
            (theme.left, theme.top),
            title,
            font=theme.font(theme.heading_size, bold=True),
            fill=theme.accent,
        )
        rule_y = theme.top + theme.rule_offset
        draw.line(
            [(theme.left, rule_y), (theme.width - theme.right, rule_y)],
            fill=theme.muted,
            width=3,
        )
        return rule_y + theme.body_offset

    def _title(self) -> Image.Image:
        theme = self.theme
        image, draw = self._canvas()
        y = self._heading(draw, self.lesson.topic.upper())
        body_font = theme.font(theme.body_size)
        for line in (f"Level: {self.lesson.level}", "", TITLE_HEADING):
            draw.text((theme.left, y), line, font=body_font, fill=theme.text)
            y += theme.line_height + theme.entry_gap
        return image

    def _word(self, entry: VocabEntry) -> Image.Image:
        theme = self.theme
        image, draw = self._canvas()
        draw.rectangle([(0, 0), (theme.width, theme.accent_bar_height)], fill=theme.accent)

        word_font = theme.font(theme.word_size, bold=True)
        ipa_font = theme.ipa_font(theme.ipa_size)
        meaning_font = theme.font(theme.meaning_size)

        word_lines = text_utils.wrap_plain(draw, entry.word, word_font, theme.max_width)
        ipa_lines = (
            text_utils.wrap_plain(draw, entry.ipa, ipa_font, theme.max_width)
            if entry.ipa
            else []
        )
        meaning_lines = (
            text_utils.wrap_plain(
                draw, entry.meaning, meaning_font, theme.max_width - theme.meaning_inset
            )
            if entry.meaning
            else []
        )

        # Measure the whole stack before drawing any of it, so the slide sits
        # optically centred on any canvas height instead of at an offset tuned
        # for one particular one. A word with a two-line meaning therefore
        # centres just as well as a bare word.
        total = text_utils.block_height(word_lines, word_font) + theme.word_ipa_gap
        if ipa_lines:
            total += text_utils.block_height(ipa_lines, ipa_font) + theme.ipa_rule_gap
        if meaning_lines:
            total += theme.rule_meaning_gap + text_utils.block_height(
                meaning_lines, meaning_font
            )

        y = (theme.height - total) / 2
        y = text_utils.draw_centered(draw, word_lines, word_font, y, theme.text, theme.width)
        y += theme.word_ipa_gap

        if ipa_lines:
            y = text_utils.draw_centered(
                draw, ipa_lines, ipa_font, y, theme.accent, theme.width
            )
            y += theme.ipa_rule_gap

        if meaning_lines:
            centre = theme.width / 2
            draw.line(
                [(centre - theme.rule_half_width, y), (centre + theme.rule_half_width, y)],
                fill=theme.muted,
                width=2,
            )
            y += theme.rule_meaning_gap
            text_utils.draw_centered(
                draw, meaning_lines, meaning_font, y, theme.muted, theme.width
            )

        return image

    def _paragraph(self, page: Sequence[Sequence[text_utils.Token]]) -> Image.Image:
        theme = self.theme
        image, draw = self._canvas()
        y = self._heading(draw, PARAGRAPH_HEADING)

        # A page rarely fills a 9:16 canvas, and text pinned under the heading
        # leaves the bottom two-thirds empty. Centring the block in whatever
        # room is left keeps the slide balanced at any aspect ratio.
        y += max(0, (theme.content_height - len(page) * theme.line_height) / 2)

        body_font = theme.font(theme.body_size)
        bold_body_font = theme.font(theme.body_size, bold=True)
        for line in page:
            text_utils.draw_token_line(
                draw, line, theme.left, y, body_font, bold_body_font, theme.text, theme.accent
            )
            y += theme.line_height
        return image


@dataclass(frozen=True)
class PillowSlidePainter:
    theme: Theme

    def prepare(self, lesson: Lesson) -> PreparedSlides:
        probe = Image.new("RGB", (self.theme.width, self.theme.height), self.theme.background)
        draw = ImageDraw.Draw(probe)
        body_font = self.theme.font(self.theme.body_size)

        lines = text_utils.wrap_tokens(
            draw, lesson.highlight_paragraph(), body_font, self.theme.max_width
        )
        pages: List = text_utils.paginate(lines, self.theme.lines_per_page)

        return PreparedSlides(theme=self.theme, lesson=lesson, paragraph_pages=pages)
