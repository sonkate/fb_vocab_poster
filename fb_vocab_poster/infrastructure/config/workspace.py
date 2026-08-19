"""Where files go, and what time it is — the two bits of ambient state the use
cases refuse to look up for themselves."""
import os
from dataclasses import dataclass
from datetime import datetime


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

    def narration_audio(self, basename: str) -> str:
        self._ensure(self.output_dir)
        return os.path.join(self.output_dir, f"{basename}.mp3")

    def narration_workdir(self, basename: str) -> str:
        return self._ensure(os.path.join(self.output_dir, f"_audio_{basename}"))

    def video(self, basename: str) -> str:
        self._ensure(self.output_dir)
        return os.path.join(self.output_dir, f"{basename}.mp4")

    def slides_workdir(self, basename: str) -> str:
        return self._ensure(os.path.join(self.output_dir, f"_slides_{basename}"))


class SystemClock:
    """Implements `application.ports.Clock`."""

    def now(self) -> datetime:
        return datetime.now()
