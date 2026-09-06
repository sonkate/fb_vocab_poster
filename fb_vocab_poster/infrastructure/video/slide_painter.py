"""Draws lesson slides with Pillow — no ImageMagick anywhere in the pipeline.

The painter answers two questions for the renderer: how many pages the
paragraph needs (which the domain needs before it can allocate screen time),
and what each requested slide looks like as a PNG.
"""
import os
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from PIL import Image, ImageDraw

from ...domain import (
    MISTAKE,
    OUTRO,
    PARAGRAPH,
    UPGRADE,
    WORD,
    Lesson,
    SlideRequest,
    VocabEntry,
)
from . import text as text_utils
from .theme import Theme

PARAGRAPH_HEADING = "READ ALONG"
ARROW = "↓"


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
        if request.kind == OUTRO:
            image = self._outro()
        elif request.kind == WORD:
            image = self._word(request.vocab)
        elif request.kind in (MISTAKE, UPGRADE):
            image = self._contrast(request.vocab)
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

    def _frame(self, draw) -> Tuple[float, float]:
        """Draws the fixed chrome — wordmark top left, level chip top right,
        series label along the foot — and returns the band of canvas left for
        the slide's own content.

        Three formats look nothing alike, but these three marks never move.
        That is what makes a slide recognisable a second into a scroll, and it
        is also what anchors the top and bottom of the canvas: content centres
        in the band between them rather than floating in an empty screen.
        """
        theme = self.theme
        draw.rectangle([(0, 0), (theme.width, theme.accent_bar_height)], fill=theme.accent)

        mark_font = theme.font(theme.chrome_size, bold=True)
        lead = f"{theme.brand_lead} "
        lead_width = draw.textlength(lead, font=mark_font)
        draw.text((theme.left, theme.top), lead, font=mark_font, fill=theme.text)
        draw.text(
            (theme.left + lead_width, theme.top),
            theme.brand_tail,
            font=mark_font,
            fill=theme.accent,
        )
        rule_y = theme.top + text_utils.line_height(mark_font) + theme.chrome_rule_gap
        draw.rectangle(
            [
                (theme.left, rule_y),
                (theme.left + theme.chrome_rule_width, rule_y + theme.chrome_rule_height),
            ],
            fill=theme.accent,
        )

        chip_font = theme.font(theme.chip_size, bold=True)
        level = str(self.lesson.level)
        chip_width = draw.textlength(level, font=chip_font) + theme.chip_padding_x * 2
        chip_height = text_utils.line_height(chip_font) + theme.chip_padding_y * 2
        chip_right = theme.width - theme.right
        draw.rounded_rectangle(
            [(chip_right - chip_width, theme.top), (chip_right, theme.top + chip_height)],
            radius=theme.chip_radius,
            fill=theme.level_color(self.lesson.level),
        )
        draw.text(
            (chip_right - chip_width + theme.chip_padding_x, theme.top + theme.chip_padding_y),
            level,
            font=chip_font,
            fill=theme.level_text,
        )

        series_font = theme.font(theme.series_size)
        text_utils.draw_tracked(
            draw,
            self.lesson.spec.series_caption(self.lesson.topic).upper(),
            series_font,
            theme.height - theme.bottom - text_utils.line_height(series_font),
            theme.muted,
            theme.width,
            theme.series_tracking,
        )

        return theme.content_top, theme.content_bottom

    def _heading(self, draw, title: str, top: float) -> int:
        """Draws a left-aligned heading with a rule under it, returning the y
        where body copy starts."""
        theme = self.theme
        draw.text(
            (theme.left, top),
            title,
            font=theme.font(theme.heading_size, bold=True),
            fill=theme.accent,
        )
        rule_y = top + theme.rule_offset
        draw.line(
            [(theme.left, rule_y), (theme.width - theme.right, rule_y)],
            fill=theme.muted,
            width=3,
        )
        return rule_y + theme.body_offset

    def _outro(self) -> Image.Image:
        """The closing brand card: wordmark, tagline, and what was just taught.

        The only slide that wears no frame: it *is* the wordmark, full size and
        centred, so a corner copy of it would just be the same mark twice.
        """
        theme = self.theme
        image, draw = self._canvas()

        mark_font = theme.font(theme.outro_mark_size, bold=True)
        detail_font = theme.font(theme.outro_detail_size)

        lead = f"{theme.brand_lead} "
        lead_width = draw.textlength(lead, font=mark_font)
        mark_width = lead_width + draw.textlength(theme.brand_tail, font=mark_font)

        mark_leading = text_utils.line_height(mark_font)
        detail_leading = text_utils.line_height(detail_font)
        total = (
            mark_leading
            + theme.word_ipa_gap
            + theme.accent_bar_height
            + theme.rule_meaning_gap
            + detail_leading * 2
        )

        y = (theme.height - total) / 2
        x = (theme.width - mark_width) / 2
        draw.text((x, y), lead, font=mark_font, fill=theme.text)
        draw.text((x + lead_width, y), theme.brand_tail, font=mark_font, fill=theme.accent)
        y += mark_leading + theme.word_ipa_gap

        draw.rectangle(
            [(x, y), (x + mark_width, y + theme.accent_bar_height)], fill=theme.accent
        )
        y += theme.accent_bar_height + theme.rule_meaning_gap

        y = text_utils.draw_centered(
            draw, [theme.tagline], detail_font, y, theme.text, theme.width
        )
        text_utils.draw_centered(
            draw,
            [f"{self.lesson.topic} · {self.lesson.level}"],
            detail_font,
            y,
            theme.muted,
            theme.width,
        )
        return image

    def _fit_word_font(self, draw, word: str):
        """Largest size at or below `word_size` that keeps the word on one
        line. Text width is near enough linear in point size that scaling by
        the measured overflow lands in one step, and flooring keeps it inside
        the frame."""
        theme = self.theme
        font = theme.font(theme.word_size, bold=True)
        width = draw.textlength(word, font=font)
        if width <= theme.max_width:
            return font
        fitted = int(theme.word_size * theme.max_width / width)
        return theme.font(max(theme.word_size_min, fitted), bold=True)

    def _word(self, entry: VocabEntry) -> Image.Image:
        theme = self.theme
        image, draw = self._canvas()
        content_top, content_bottom = self._frame(draw)

        word_font = self._fit_word_font(draw, entry.word)
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

        y = content_top + (content_bottom - content_top - total) / 2
        y = text_utils.draw_centered(draw, word_lines, word_font, y, theme.accent, theme.width)
        y += theme.word_ipa_gap

        if ipa_lines:
            y = text_utils.draw_centered(
                draw, ipa_lines, ipa_font, y, theme.muted, theme.width
            )
            y += theme.ipa_rule_gap

        if meaning_lines:
            centre = theme.width / 2
            draw.line(
                [(centre - theme.rule_half_width, y), (centre + theme.rule_half_width, y)],
                fill=theme.accent_soft,
                width=theme.rule_thickness,
            )
            y += theme.rule_meaning_gap
            text_utils.draw_centered(
                draw, meaning_lines, meaning_font, y, theme.text_soft, theme.width
            )

        return image

    def _contrast(self, entry: VocabEntry) -> Image.Image:
        """Before above, after below: the shared layout of every format that
        teaches by opposition — a mistake and its correction, a weak phrase and
        its upgrade. Which of the two the viewer is looking at is named by the
        series label at the foot, drawn by `_frame`."""
        theme = self.theme
        image, draw = self._canvas()
        content_top, content_bottom = self._frame(draw)

        before, after, note = entry.columns
        from_font = theme.font(theme.contrast_from_size)
        arrow_font = theme.ipa_font(theme.contrast_from_size)
        to_font = theme.font(theme.contrast_to_size, bold=True)
        note_font = theme.font(theme.meaning_size)

        before_lines = text_utils.wrap_plain(draw, before, from_font, theme.max_width)
        after_lines = text_utils.wrap_plain(draw, after, to_font, theme.max_width)
        note_lines = (
            text_utils.wrap_plain(
                draw, note, note_font, theme.max_width - theme.meaning_inset
            )
            if note
            else []
        )

        total = (
            text_utils.block_height(before_lines, from_font)
            + text_utils.line_height(arrow_font)
            + text_utils.block_height(after_lines, to_font)
        )
        if note_lines:
            total += theme.rule_meaning_gap + text_utils.block_height(note_lines, note_font)

        y = content_top + (content_bottom - content_top - total) / 2
        y = text_utils.draw_centered(
            draw, before_lines, from_font, y, theme.danger, theme.width
        )
        y = text_utils.draw_centered(
            draw, [ARROW], arrow_font, y, theme.muted, theme.width
        )
        y = text_utils.draw_centered(
            draw, after_lines, to_font, y, theme.accent, theme.width
        )

        if note_lines:
            y += theme.rule_meaning_gap
            text_utils.draw_centered(
                draw, note_lines, note_font, y, theme.muted, theme.width
            )
        return image

    def _paragraph(self, page: Sequence[Sequence[text_utils.Token]]) -> Image.Image:
        theme = self.theme
        image, draw = self._canvas()
        content_top, content_bottom = self._frame(draw)

        # Heading, rule and text move as one block: a page rarely fills a 9:16
        # canvas, and centring the whole thing in the content band keeps the
        # heading over its own copy rather than stranded at the top edge.
        total = theme.rule_offset + theme.body_offset + len(page) * theme.line_height
        y = self._heading(
            draw, PARAGRAPH_HEADING, content_top + max(0, (content_bottom - content_top - total) / 2)
        )

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
