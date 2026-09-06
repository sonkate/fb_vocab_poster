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
