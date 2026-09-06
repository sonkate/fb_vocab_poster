"""Use case: put the drafts already on disk into the ledger.

The ledger is written when a lesson is drafted, so a database switched on later
starts empty while `drafts/` already holds every lesson ever written. This
replays that history into it.
"""
from dataclasses import dataclass, field
from typing import List, Tuple

from ..blank_form import is_blank_form
from ..ports import DraftRepository, ProgressReporter, VocabularyLedger


@dataclass(frozen=True)
class BackfillReport:
    recorded: Tuple[str, ...] = ()
    skipped: Tuple[Tuple[str, str], ...] = ()

    @property
    def total(self) -> int:
        return len(self.recorded) + len(self.skipped)


@dataclass(frozen=True)
class BackfillLedger:
    repository: DraftRepository
    ledger: VocabularyLedger
    reporter: ProgressReporter

    def __call__(self) -> BackfillReport:
        recorded: List[str] = []
        skipped: List[Tuple[str, str]] = []

        for identifier in self.repository.identifiers():
            ref = self.repository.reference(identifier)
            try:
                lesson = self.repository.load(identifier)
            except Exception as error:
                # One unreadable draft must not abandon the other eight.
                skipped.append((ref.basename, str(error)))
                continue

            if is_blank_form(lesson):
                skipped.append((ref.basename, "still a blank template"))
                continue
            if not lesson.vocab:
                skipped.append((ref.basename, "no rows"))
                continue

            self.ledger.record(lesson, ref)
            recorded.append(ref.basename)
            self.reporter.step(
                f"  recorded {ref.basename} "
                f"({lesson.topic} {lesson.level}, {len(lesson.vocab)} rows)"
            )

        return BackfillReport(recorded=tuple(recorded), skipped=tuple(skipped))
