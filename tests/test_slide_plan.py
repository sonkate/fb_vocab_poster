from fb_vocab_poster.domain import (
    NarrationSegment,
    NarrationTiming,
    VocabEntry,
    build_slide_plan,
    word_segment_duration,
)

TIMELINE = (
    NarrationSegment(kind="word", duration=3.0, vocab=VocabEntry(word="hello")),
    NarrationSegment(kind="paragraph", duration=12.0),
    NarrationSegment(kind="outro", duration=2.2),
)


def test_one_slide_per_narration_segment_when_paragraph_fits_one_page():
    plan = build_slide_plan(TIMELINE, paragraph_pages=1)

    assert [slide.kind for slide in plan] == ["word", "paragraph", "outro"]
    assert [slide.duration for slide in plan] == [3.0, 12.0, 2.2]


def test_the_brand_card_closes_the_video_rather_than_opening_it():
    """The first seconds decide whether a viewer stays, so they go to content."""
    plan = build_slide_plan(TIMELINE, paragraph_pages=2)

    assert plan[0].kind == "word"
    assert plan[-1].kind == "outro"


def test_paragraph_time_is_split_evenly_across_its_pages():
    plan = build_slide_plan(TIMELINE, paragraph_pages=3)

    paragraph_slides = [slide for slide in plan if slide.kind == "paragraph"]
    assert [slide.duration for slide in paragraph_slides] == [4.0, 4.0, 4.0]
    assert [slide.page for slide in paragraph_slides] == [0, 1, 2]


def test_slide_durations_always_sum_to_the_narration_length():
    plan = build_slide_plan(TIMELINE, paragraph_pages=4)

    assert sum(slide.duration for slide in plan) == sum(s.duration for s in TIMELINE)


def test_word_duration_covers_both_readings_and_the_pauses_around_them():
    timing = NarrationTiming(pause_between_slow_fast=0.5, pause_after_word=0.8)

    assert word_segment_duration(1.0, 0.7, timing) == 3.0
