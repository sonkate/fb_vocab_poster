"""Domain-level failures. These carry no knowledge of CLIs, HTTP or files."""


class DomainError(Exception):
    """Base class for every error the domain raises."""


class InvalidLevelError(DomainError):
    """The requested CEFR level is not one this system teaches."""


class IncompleteLessonError(DomainError):
    """A lesson is missing the parts needed to render or publish it."""


class InvalidLessonFile(DomainError):
    """A stored draft could not be read back as a lesson."""
