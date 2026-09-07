from fb_vocab_poster.infrastructure.video.text import paginate


def test_pagination_needs_no_splitting_when_everything_fits_one_page():
    lines = ["one", "two", "three"]

    assert paginate(lines, per_page=5) == [["one", "two", "three"]]


def test_an_empty_paragraph_still_yields_one_page():
    assert paginate([], per_page=5) == [[]]


def test_pagination_spreads_the_overflow_instead_of_stranding_it_alone():
    """13 lines at 12/page used to give an 12-then-1 split — a near-empty
    final page. Balancing lands on 7-then-6 instead."""
    lines = list(range(13))

    pages = paginate(lines, per_page=12)

    assert [len(page) for page in pages] == [7, 6]
    assert pages[0] + pages[1] == lines


def test_pagination_never_leaves_pages_more_than_one_line_apart():
    lines = list(range(23))

    pages = paginate(lines, per_page=10)

    sizes = [len(page) for page in pages]
    assert max(sizes) - min(sizes) <= 1
    assert sum(sizes) == len(lines)
