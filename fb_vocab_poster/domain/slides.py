"""Which slides a lesson produces, and how long each one is on screen.

Deciding *what* to show and *for how long* is policy; drawing pixels is not.
Only the former lives here — the paragraph's page count is passed in, because
that depends on the font metrics of whatever renderer is in use.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .lesson_format import PARAGRAPH
from .narration import NarrationSegment
from .lesson import VocabEntry


@dataclass(frozen=True)
class SlideRequest:
    """A slide to draw, and the seconds it should hold."""

    kind: str
    duration: float
    vocab: Optional[VocabEntry] = None
    page: int = 0
    page_count: int = 1


def build_slide_plan(
    segments: Sequence[NarrationSegment], paragraph_pages: int = 1
) -> List[SlideRequest]:
    """Maps the narration timeline onto slides. A paragraph long enough to need
    several pages splits its narration time evenly across them."""
    pages = max(1, paragraph_pages)
    plan: List[SlideRequest] = []

    for segment in segments:
        if segment.kind == PARAGRAPH:
            per_page = segment.duration / pages
            plan.extend(
                SlideRequest(
                    kind=PARAGRAPH, duration=per_page, page=page, page_count=pages
                )
                for page in range(pages)
            )
        else:
            # A segment's kind is already the layout its format asked for, so
            # a new format needs no branch here — only a painter.
            plan.append(
                SlideRequest(
                    kind=segment.kind, duration=segment.duration, vocab=segment.vocab
                )
            )

    return plan
