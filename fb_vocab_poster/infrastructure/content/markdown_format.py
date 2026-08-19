"""Translation between a `Lesson` and the markdown a human edits.

The markdown file is the review surface of this whole system, so its shape is
pinned down in exactly one place: here.
"""
import re
from typing import Dict, List

from ...domain import CEFRLevel, InvalidLessonFile, Lesson, VocabEntry

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
FIELD_SEPARATOR = "—"

VOCABULARY = "Vocabulary"
PARAGRAPH = "Paragraph"
CAPTION = "Caption"


def _frontmatter(text: str):
    match = FRONTMATTER.search(text)
    if not match:
        return {}, text
    meta: Dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip()
    return meta, text[match.end():]


def _section(text: str, name: str) -> str:
    match = re.search(
        rf"##\s*{name}\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL | re.IGNORECASE
    )
    return match.group(1).strip() if match else ""


def _parse_vocab(block: str) -> List[VocabEntry]:
    entries: List[VocabEntry] = []
    for raw_line in block.splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(FIELD_SEPARATOR)]
        if len(parts) >= 3:
            entries.append(VocabEntry(word=parts[0], ipa=parts[1], meaning=parts[2]))
        elif parts[0]:
            entries.append(VocabEntry(word=parts[0]))
    return entries


def parse(text: str, source: str = "<draft>") -> Lesson:
    meta, body = _frontmatter(text)

    raw_level = meta.get("level", "")
    if not raw_level:
        raise InvalidLessonFile(
            f"{source} has no `level:` in its frontmatter — add e.g. `level: B1`."
        )
    level = CEFRLevel.parse(raw_level)

    return Lesson(
        topic=meta.get("topic", ""),
        level=level,
        vocab=tuple(_parse_vocab(_section(body, VOCABULARY))),
        # Bold markers help a human reader but would be read aloud and drawn
        # literally, so they come off here.
        paragraph=_section(body, PARAGRAPH).replace("**", ""),
        caption=_section(body, CAPTION),
    )


def render(lesson: Lesson) -> str:
    """Serialises a lesson back into the same format `parse` accepts."""
    lines = [
        "---",
        f"topic: {lesson.topic}",
        f"level: {lesson.level}",
        "---",
        "",
        f"## {VOCABULARY}",
    ]
    for entry in lesson.vocab:
        lines.append(
            f"- {entry.word} {FIELD_SEPARATOR} {entry.ipa} {FIELD_SEPARATOR} {entry.meaning}"
        )
    lines += ["", f"## {PARAGRAPH}", lesson.paragraph.strip(), "", f"## {CAPTION}", lesson.caption.strip(), ""]
    return "\n".join(lines)
