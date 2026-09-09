import pytest

from fb_vocab_poster.domain import (
    Fragment,
    NarrationSegment,
    NarrationTiming,
    VocabEntry,
    build_slide_plan,
    page_word_counts,
    word_segment_duration,
)

TIMELINE = (
    NarrationSegment(kind="word", duration=3.0, vocab=VocabEntry(word="hello")),
    NarrationSegment(kind="paragraph", duration=12.0),
    NarrationSegment(kind="outro", duration=2.2),
)


def test_one_slide_per_narration_segment_when_paragraph_fits_one_page():
    plan = build_slide_plan(TIMELINE, paragraph_page_weights=(1,))

    assert [slide.kind for slide in plan] == ["word", "paragraph", "outro"]
    assert [slide.duration for slide in plan] == [3.0, 12.0, 2.2]


def test_a_non_paragraph_segments_stage_carries_through_to_its_slide():
    """A contrast-rhythm row's two segments (wrong/full) each become their own
    slide, and the painter needs to know which half it's drawing."""
    timeline = (
        NarrationSegment(kind="mistake", duration=2.0, stage="wrong"),
        NarrationSegment(kind="mistake", duration=5.0, stage="full"),
    )

    plan = build_slide_plan(timeline)

    assert [slide.stage for slide in plan] == ["wrong", "full"]


def test_the_brand_card_closes_the_video_rather_than_opening_it():
    """The first seconds decide whether a viewer stays, so they go to content."""
    plan = build_slide_plan(TIMELINE, paragraph_page_weights=(1, 1))

    assert plan[0].kind == "word"
    assert plan[-1].kind == "outro"


def test_paragraph_time_is_split_evenly_across_equally_weighted_pages():
    plan = build_slide_plan(TIMELINE, paragraph_page_weights=(1, 1, 1))

    paragraph_slides = [slide for slide in plan if slide.kind == "paragraph"]
    assert [slide.duration for slide in paragraph_slides] == [4.0, 4.0, 4.0]
    assert [slide.page for slide in paragraph_slides] == [0, 1, 2]


def test_paragraph_time_follows_each_pages_share_of_the_words():
    """A page holding three times the words of another should hold the screen
    three times as long. Splitting evenly instead — the bug this fixes — let
    a light page linger just as long as a packed one, so the narration was
    already onto the next page while that one was still on screen."""
    plan = build_slide_plan(TIMELINE, paragraph_page_weights=(30, 10))

    paragraph_slides = [slide for slide in plan if slide.kind == "paragraph"]
    assert [slide.duration for slide in paragraph_slides] == [9.0, 3.0]


def test_slide_durations_always_sum_to_the_narration_length():
    plan = build_slide_plan(TIMELINE, paragraph_page_weights=(2, 5, 1, 3))

    assert sum(slide.duration for slide in plan) == pytest.approx(
        sum(s.duration for s in TIMELINE)
    )


def test_word_duration_covers_both_readings_and_the_pauses_around_them():
    timing = NarrationTiming(pause_between_slow_fast=0.5, pause_after_word=0.8)

    assert word_segment_duration(1.0, 0.7, timing) == 3.0


def test_page_word_counts_counts_only_fragments_that_start_a_word():
    page_one = [
        [Fragment("Hello"), Fragment(",", starts_word=False), Fragment("world")]
    ]
    page_two = [[Fragment("Hi")], [Fragment("there")]]

    assert page_word_counts([page_one, page_two]) == [2, 2]


def test_page_word_counts_treats_an_empty_page_as_one_word_to_avoid_a_zero_share():
    assert page_word_counts([[]]) == [1]


def test_a_hook_segment_fans_out_one_slide_per_word_when_a_hook_line_is_given():
    timeline = (NarrationSegment(kind="hook", duration=4.0),)

    plan = build_slide_plan(timeline, hook_line="Nói tiếng Anh nghe tự nhiên")

    assert [slide.kind for slide in plan] == ["hook"] * 6
    assert [slide.page for slide in plan] == [0, 1, 2, 3, 4, 5]
    assert [slide.page_count for slide in plan] == [6] * 6


def test_a_hook_word_holds_the_screen_for_an_even_share_regardless_of_length():
    """The hook is always Vietnamese, spoken one syllable ("tiếng") per
    space-separated word, and syllables take about the same time to say no
    matter how many letters spell them. Splitting by character count instead
    (the bug this fixes) let a short quoted loanword like "'vibe'" claim as
    much of the pill's timeline as two full syllables — badly out of step
    with the real recording."""
    timeline = (NarrationSegment(kind="hook", duration=9.0),)

    plan = build_slide_plan(timeline, hook_line="a bb cccc")

    assert [slide.duration for slide in plan] == pytest.approx([3.0, 3.0, 3.0])


def test_a_hook_segments_lead_in_becomes_its_own_resting_slide():
    """`lead_in` is silence the adapter measured before the voice actually
    starts — the pill has nothing to sweep across yet, so that stretch gets
    its own unhighlighted slide (`page=-1`) instead of starting the sweep
    before anyone is speaking."""
    timeline = (NarrationSegment(kind="hook", duration=4.0, lead_in=1.0),)

    plan = build_slide_plan(timeline, hook_line="one two")

    assert [slide.page for slide in plan] == [-1, 0, 1]
    assert plan[0].duration == pytest.approx(1.0)
    assert plan[0].fade_in is True
    assert [slide.fade_in for slide in plan[1:]] == [False, False]
    assert sum(slide.duration for slide in plan[1:]) == pytest.approx(3.0)


def test_a_hook_segments_trail_out_is_folded_into_holding_the_last_word():
    """`trail_out` is dead air after the voice finishes — the clip's own
    trailing silence plus the breathing pause after it. The sweep has
    already caught up with the sentence by then, so it just holds the last
    word rather than adding a separate state nothing asked for."""
    timeline = (NarrationSegment(kind="hook", duration=5.0, trail_out=2.0),)

    plan = build_slide_plan(timeline, hook_line="one two")

    assert [slide.duration for slide in plan] == pytest.approx([1.5, 3.5])


def test_only_the_first_hook_word_fades_in_the_rest_continue_the_reveal():
    timeline = (NarrationSegment(kind="hook", duration=4.0),)

    plan = build_slide_plan(timeline, hook_line="one two three")

    assert [slide.fade_in for slide in plan] == [True, False, False]


def test_a_blank_hook_line_leaves_the_hook_segment_as_a_single_unhighlighted_slide():
    """Backward compatibility: a caller that never passes `hook_line` (the
    default) must get exactly what it always got — one slide, not a crash
    or an empty plan."""
    timeline = (NarrationSegment(kind="hook", duration=4.0),)

    plan = build_slide_plan(timeline)

    assert [slide.kind for slide in plan] == ["hook"]
    assert plan[0].duration == 4.0
    assert plan[0].fade_in is True


def test_every_non_hook_non_paragraph_slide_still_fades_in_by_default():
    plan = build_slide_plan(TIMELINE, paragraph_page_weights=(1, 1))

    assert all(slide.fade_in for slide in plan)
