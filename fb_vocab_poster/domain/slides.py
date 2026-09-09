"""Which slides a lesson produces, and how long each one is on screen.

Deciding *what* to show and *for how long* is policy; drawing pixels is not.
Only the former lives here — the paragraph's per-page word counts are passed
in, because how the text wraps into pages depends on the font metrics of
whatever renderer is in use. The hook's word-by-word split needs no such
help: it is plain string splitting, so it happens right here.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

from .lesson import Fragment, VocabEntry
from .lesson_format import HOOK, PARAGRAPH
from .narration import NarrationSegment


@dataclass(frozen=True)
class SlideRequest:
    """A slide to draw, and the seconds it should hold."""

    kind: str
    duration: float
    vocab: Optional[VocabEntry] = None
    # Doubles as the paragraph page index/count, and — for a fanned-out hook
    # word — the currently-highlighted word's index and the hook's total
    # word count.
    page: int = 0
    page_count: int = 1
    stage: str = "full"   # "wrong" or "full" — which half of a contrast-rhythm row this is
    # False only for a hook word that continues the same reveal its
    # predecessor started — see `build_slide_plan`. Every other slide fades
    # in on its own, unaffected by this field's default.
    fade_in: bool = True


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
    hook_line: str = "",
) -> List[SlideRequest]:
    """Maps the narration timeline onto slides. A paragraph long enough to need
    several pages splits its narration time in proportion to each page's word
    count, so a page with more to read holds the screen longer than one with
    less — not for an equal, word-count-blind share.

    The hook segment fans out the same way, one slide per word: a longer word
    takes longer to say, so it holds the screen in proportion to its own
    character count rather than getting the same slice as a short one. Every
    word after the first continues the same reveal instead of fading in on
    its own — see `SlideRequest.fade_in`. `hook_line` is only needed to know
    where the words split; leaving it blank (any caller that predates this
    fan-out) keeps a hook segment as the single, unhighlighted slide it
    always was.
    """
    weights = list(paragraph_page_weights) or [1]
    total_weight = sum(weights)
    hook_words = hook_line.split()
    hook_weights = [len(word) for word in hook_words] or [1]
    hook_total_weight = sum(hook_weights)
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
        elif segment.kind == HOOK and hook_words:
            plan.extend(
                SlideRequest(
                    kind=HOOK,
                    duration=segment.duration * weight / hook_total_weight,
                    page=word_index,
                    page_count=len(hook_words),
                    fade_in=(word_index == 0),
                )
                for word_index, weight in enumerate(hook_weights)
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
