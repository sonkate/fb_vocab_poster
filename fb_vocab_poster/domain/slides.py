"""Which slides a lesson produces, and how long each one is on screen.

Deciding *what* to show and *for how long* is policy; drawing pixels is not.
Only the former lives here — the paragraph's per-page word counts are passed
in, because how the text wraps into pages depends on the font metrics of
whatever renderer is in use.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .lesson import Fragment, VocabEntry
from .lesson_format import PARAGRAPH
from .narration import NarrationSegment


@dataclass(frozen=True)
class SlideRequest:
    """A slide to draw, and the seconds it should hold."""

    kind: str
    duration: float
    vocab: Optional[VocabEntry] = None
    page: int = 0
    page_count: int = 1
    stage: str = "full"   # "wrong" or "full" — which half of a contrast-rhythm row this is


def page_word_counts(pages: Sequence[Sequence[Sequence[Fragment]]]) -> List[int]:
    """Words on each paragraph page, so its narration time can be weighted by
    how much there actually is to read rather than split evenly. Word-wrap
    packs a different number of words onto each page depending on how long
    they are, so an even split reliably drifts out of sync with the audio —
    a page counted as empty still holds for a token share rather than none."""
    return [
        sum(1 for line in page for fragment in line if fragment.starts_word) or 1
        for page in pages
    ]


def build_slide_plan(
    segments: Sequence[NarrationSegment],
    paragraph_page_weights: Sequence[int] = (1,),
) -> List[SlideRequest]:
    """Maps the narration timeline onto slides. A paragraph long enough to need
    several pages splits its narration time in proportion to each page's word
    count, so a page with more to read holds the screen longer than one with
    less — not for an equal, word-count-blind share."""
    weights = list(paragraph_page_weights) or [1]
    total_weight = sum(weights)
    plan: List[SlideRequest] = []

    for segment in segments:
        if segment.kind == PARAGRAPH:
            plan.extend(
                SlideRequest(
                    kind=PARAGRAPH,
                    duration=segment.duration * weight / total_weight,
                    page=page,
                    page_count=len(weights),
                )
                for page, weight in enumerate(weights)
            )
        else:
            # A segment's kind is already the layout its format asked for, so
            # a new format needs no branch here — only a painter.
            plan.append(
                SlideRequest(
                    kind=segment.kind,
                    duration=segment.duration,
                    vocab=segment.vocab,
                    stage=segment.stage,
                )
            )

    return plan
