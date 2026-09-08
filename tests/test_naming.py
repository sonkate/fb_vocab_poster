from datetime import datetime

from fb_vocab_poster.domain.level import CEFRLevel
from fb_vocab_poster.domain.naming import basename_month, draft_basename, slugify


def test_a_vietnamese_topic_transliterates_instead_of_losing_its_letters():
    """Dropping accents used to leave only the consonants (`công việc` ->
    `c-ng-vi-c`) — every draft/output filename must stay readable ASCII."""
    assert slugify("Email công việc") == "email-cong-viec"
    assert slugify("Đừng nói X, nói Y") == "dung-noi-x-noi-y"
    assert slugify("Bẫy phát âm") == "bay-phat-am"


def test_an_already_ascii_topic_is_unaffected():
    assert slugify("Ordering Coffee") == "ordering-coffee"


def test_draft_basename_stays_ascii_end_to_end():
    when = datetime(2026, 1, 1, 12, 0, 0)

    assert draft_basename("Email công việc", CEFRLevel.B1, when) == (
        "email-cong-viec_B1_20260101-120000"
    )


def test_basename_month_reads_the_month_out_of_the_basenames_own_timestamp():
    """The output folder a video lands in comes from when the draft was
    created, not whatever day `build` happens to run — so a re-render months
    later still lands back in the original month's folder."""
    assert basename_month("work-email_B1_20260908-231010") == "2026-09"
    assert basename_month("ordering-coffee_B1_20260101-120000") == "2026-01"
