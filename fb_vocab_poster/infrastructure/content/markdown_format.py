"""Translation between a `Lesson` and the markdown a human edits.

The markdown file is the review surface of this whole system, so its shape is
pinned down in exactly one place: here.
"""
import re
from typing import Dict, List, Sequence

from ...domain import (
    CEFRLevel,
    InvalidLessonFile,
    Lesson,
    LessonFormat,
    VocabEntry,
    spec_for,
)

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
FIELD_SEPARATOR = "—"

AVOID_NOTE = "Đã dạy ở bài trước, đừng dùng lại"

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
        line = raw_line.strip()
        if line.startswith("<!--"):   # the column legend `render` writes
            continue
        line = line.lstrip("-").strip()
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
    lesson_format = LessonFormat.parse(meta.get("format", ""))
    spec = spec_for(lesson_format)

    return Lesson(
        topic=meta.get("topic", ""),
        level=level,
        format=lesson_format,
        vocab=tuple(_parse_vocab(_section(body, spec.section))),
        # The bold markers stay: they are how the draft says which words the
        # slide teaches, and only the code that speaks or posts the paragraph
        # takes them off.
        paragraph=_section(body, PARAGRAPH),
        caption=_section(body, CAPTION),
    )


def render(lesson: Lesson, avoid: Sequence[str] = ()) -> str:
    """Serialises a lesson back into the same format `parse` accepts.

    `avoid` is written in as a comment rather than as content: most drafts are
    still filled in by hand, and whoever fills this one in needs the
    already-taught list in front of them. `_parse_vocab` drops comment lines,
    so the note never survives back into a `Lesson`.
    """
    spec = lesson.spec
    lines = [
        "---",
        f"topic: {lesson.topic}",
        f"level: {lesson.level}",
        f"format: {lesson.format}",
        "---",
        "",
        f"## {spec.section}",
        # The columns differ per format, so the file says which is which
        # rather than leaving a reviewer to infer it from the rows.
        f"<!-- {f' {FIELD_SEPARATOR} '.join(spec.columns)} -->",
    ]
    if avoid:
        lines.append(f"<!-- {AVOID_NOTE}: {', '.join(avoid)} -->")
    for entry in lesson.vocab:
        lines.append(
            f"- {entry.word} {FIELD_SEPARATOR} {entry.ipa} {FIELD_SEPARATOR} {entry.meaning}"
        )
    if spec.needs_paragraph:
        lines += ["", f"## {PARAGRAPH}", lesson.paragraph.strip()]
    lines += ["", f"## {CAPTION}", lesson.caption.strip(), ""]
    return "\n".join(lines)
