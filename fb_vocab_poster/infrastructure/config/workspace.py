"""Where files go, and what time it is — the two bits of ambient state the use
cases refuse to look up for themselves."""
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ...domain.naming import basename_month

# Technical junk — narration audio and the per-slide intermediates — lives
# under its own subtree, apart from the finished videos a user actually
# opens. It isn't split by month: it's keyed by basename alone, so nothing
# needs to look it up twice.
_WORK_SUBDIR = "_work"


@dataclass(frozen=True)
class FileSystemWorkspace:
    """Implements `application.ports.Workspace` against a local output dir.

    Directories are created on demand rather than at import time, so simply
    importing this module never touches the disk.
    """

    output_dir: str

    def _ensure(self, path: str) -> str:
        os.makedirs(path, exist_ok=True)
        return path

    def _work_dir(self) -> str:
        return self._ensure(os.path.join(self.output_dir, _WORK_SUBDIR))

    def _month_dir(self, basename: str) -> str:
        return self._ensure(os.path.join(self.output_dir, basename_month(basename)))

    def _legacy_video(self, basename: str) -> str:
        """Where a video would have landed before videos were split into
        month folders — checked as a fallback so a basename rendered under
        the old flat layout is still found during the transition, without
        needing every old file moved by hand."""
        return os.path.join(self.output_dir, f"{basename}.mp4")

    def narration_audio(self, basename: str) -> str:
        return os.path.join(self._work_dir(), f"{basename}.mp3")

    def narration_workdir(self, basename: str) -> str:
        return self._ensure(os.path.join(self._work_dir(), f"_audio_{basename}"))

    def video(self, basename: str) -> str:
        return os.path.join(self._month_dir(basename), f"{basename}.mp4")

    def slides_workdir(self, basename: str) -> str:
        return self._ensure(os.path.join(self._work_dir(), f"_slides_{basename}"))

    def fresh_video(self, basename: str, since: datetime) -> Optional[str]:
        for path in (self.video(basename), self._legacy_video(basename)):
            try:
                rendered_at = datetime.fromtimestamp(os.path.getmtime(path))
            except OSError:
                continue
            if rendered_at >= since:
                return path
        return None


class SystemClock:
    """Implements `application.ports.Clock`."""

    def now(self) -> datetime:
        return datetime.now()
