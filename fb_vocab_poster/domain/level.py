"""CEFR levels, the only vocabulary difficulty scale this system speaks."""
from enum import Enum

from .errors import InvalidLevelError


class CEFRLevel(str, Enum):
    """A Common European Framework level. Inherits `str` so it formats and
    serialises as its own code ("B1") wherever plain text is expected."""

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

    @classmethod
    def parse(cls, raw: str) -> "CEFRLevel":
        """Accepts any casing/whitespace a human might type on the CLI."""
        try:
            return cls(str(raw).strip().upper())
        except ValueError:
            raise InvalidLevelError(
                f"level must be one of {', '.join(l.value for l in cls)} (got {raw!r})"
            ) from None

    def __str__(self) -> str:
        return self.value
