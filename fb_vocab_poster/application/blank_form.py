"""Telling a filled-in lesson apart from the empty form it started as.

`Lesson.ensure_publishable()` does not catch this: a blank template has both a
vocabulary section and a paragraph, they are just placeholders. Anything that
writes to the ledger needs this test, or the literal words "word", "ipa" and
"meaning" get recorded as taught and excluded from every later lesson.
"""
from ..domain import Lesson, spec_for


def is_blank_form(lesson: Lesson) -> bool:
    """True when every row is still the column legend the template lays down."""
    columns = spec_for(lesson.format).columns
    return bool(lesson.vocab) and all(
        entry.columns == columns for entry in lesson.vocab
    )
