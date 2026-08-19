"""Enterprise rules: what a lesson is, how it is narrated, how it is paced.

This package imports nothing outside the standard library — no Pillow, no
moviepy, no HTTP, no filesystem conventions beyond naming.
"""
from .errors import (
    DomainError,
    IncompleteLessonError,
    InvalidLessonFile,
    InvalidLevelError,
)
from .lesson import Lesson, VocabEntry, to_entries
from .level import CEFRLevel
from .narration import (
    PARAGRAPH,
    TITLE,
    WORD,
    NarrationSegment,
    NarrationTiming,
    SpeechCue,
    build_audio_plan,
    total_duration,
    word_segment_duration,
)
from .slides import SlideRequest, build_slide_plan

__all__ = [
    "CEFRLevel",
    "DomainError",
    "IncompleteLessonError",
    "InvalidLessonFile",
    "InvalidLevelError",
    "Lesson",
    "NarrationSegment",
    "NarrationTiming",
    "PARAGRAPH",
    "SlideRequest",
    "SpeechCue",
    "TITLE",
    "VocabEntry",
    "WORD",
    "build_audio_plan",
    "build_slide_plan",
    "to_entries",
    "total_duration",
    "word_segment_duration",
]
