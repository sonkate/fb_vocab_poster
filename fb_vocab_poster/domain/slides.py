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

    The hook segment fans out the same way, one slide per word — but split
    evenly by word count, not character count: the hook is always Vietnamese,
    and Vietnamese syllables ("tiếng") read at roughly the same pace no
    matter how many letters spell one, so a character-weighted split let a
    short quoted loanword like "'vibe'" (six characters, one syllable) claim
    as much of the pill's timeline as two full "tiếng" — badly out of step
    with the real recording. `segment.lead_in`/`trail_out` trim the fan-out to
    the span the adapter actually measured the voice occupying inside the
    clip, so the pill doesn't spend time sweeping across silence the TTS
    engine padded onto either end (or the breathing pause we add after it) —
    a leading silence becomes its own resting slide (no pill yet), and a
    trailing one is folded into holding the last word instead of a separate
    state. Every word after the first continues the same reveal instead of
    fading in on its own — see `SlideRequest.fade_in`. `hook_line` is only
    needed to know where the words split; leaving it blank (any caller that
    predates this fan-out) keeps a hook segment as the single, unhighlighted
    slide it always was.
    """
    weights = list(paragraph_page_weights) or [1]
    total_weight = sum(weights)
    hook_words = hook_line.split()
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
            voice_span = max(segment.duration - segment.lead_in - segment.trail_out, 0.001)
            per_word = voice_span / len(hook_words)
            if segment.lead_in > 0:
                plan.append(
                    SlideRequest(
                        kind=HOOK, duration=segment.lead_in, page=-1, page_count=len(hook_words)
                    )
                )
            plan.extend(
                SlideRequest(
                    kind=HOOK,
                    duration=per_word + (segment.trail_out if word_index == len(hook_words) - 1 else 0),
                    page=word_index,
                    page_count=len(hook_words),
                    fade_in=(word_index == 0 and segment.lead_in <= 0),
                )
                for word_index in range(len(hook_words))
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
