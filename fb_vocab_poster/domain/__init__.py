"""Enterprise rules: what a lesson is, how it is narrated, how it is paced.

This package imports nothing outside the standard library — no Pillow, no
moviepy, no HTTP, no filesystem conventions beyond naming.
"""
from .errors import (
    DomainError,
    IncompleteLessonError,
    InvalidLessonFile,
    InvalidLevelError,
    StaleRenderError,
)
from .lesson import Fragment, Lesson, VocabEntry, fragments_of, strip_markup, to_entries
from .lesson_format import (
    FORMATS,
    MISTAKE,
    OUTRO,
    PARAGRAPH,
    UPGRADE,
    WORD,
    FormatSpec,
    LessonFormat,
    spec_for,
)
from .level import CEFRLevel
from .narration import (
    NarrationSegment,
    NarrationTiming,
    SpeechCue,
    build_audio_plan,
    total_duration,
    word_segment_duration,
)
from .slides import SlideRequest, build_slide_plan, page_word_counts

__all__ = [
    "build_audio_plan",
    "build_slide_plan",
    "CEFRLevel",
    "DomainError",
    "FORMATS",
    "FormatSpec",
    "Fragment",
    "fragments_of",
    "IncompleteLessonError",
    "InvalidLessonFile",
    "InvalidLevelError",
    "Lesson",
    "LessonFormat",
    "MISTAKE",
    "NarrationSegment",
    "NarrationTiming",
    "OUTRO",
    "page_word_counts",
    "PARAGRAPH",
    "SlideRequest",
    "spec_for",
    "SpeechCue",
    "StaleRenderError",
    "strip_markup",
    "to_entries",
    "total_duration",
    "UPGRADE",
    "VocabEntry",
    "WORD",
    "word_segment_duration",
]
