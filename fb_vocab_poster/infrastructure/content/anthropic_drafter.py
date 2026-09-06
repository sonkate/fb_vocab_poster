"""Drafts a lesson with Claude.

Implements `application.ports.LessonDrafter`. The model is asked for the same
markdown the repository stores, so its reply goes through the one parser the
rest of the system uses — a malformed reply fails here, not three steps later.
"""
from dataclasses import dataclass
from typing import Dict, Optional, Sequence

import anthropic

from ...domain import CEFRLevel, Lesson, LessonFormat, spec_for
from . import markdown_format

DRAFT_PROMPT = """You are writing content for a Facebook page that teaches \
English to Vietnamese learners. Topic: "{topic}". CEFR level: {level}.

{avoid_block}Produce EXACTLY this markdown structure, nothing before or after it:

## {section}
{rows}

{paragraph_block}## Caption
(A short, friendly Facebook caption, 1-2 sentences, with 3-5 relevant \
hashtags, ending in a real question a reader can answer in five seconds. \
Mention the level, e.g. "Level: {level}". Never write "tag a friend", \
"comment YES" or "share if you agree" — Facebook penalises engagement bait \
at the post level.)
"""

AVOID_BLOCK = """This topic has been taught before. These have already been \
used and must NOT appear again — not one of them, in any form:
{avoid}

Choose entirely different ones that are still natural for this topic and level.

"""

PARAGRAPH_BLOCK = """## Paragraph
(A natural, engaging paragraph, 80-140 words, appropriate for {level} \
readers, that uses ALL the words above at least once. Bold each of them with \
**double asterisks** the first time it appears.)

"""

# What the three columns hold, per format. The parser only ever sees rows of
# `a — b — c`, so this is where the model is told what a, b and c mean.
ROW_INSTRUCTIONS: Dict[LessonFormat, str] = {
    LessonFormat.VOCAB: (
        "- word — /IPA pronunciation/ — short simple definition (max 12 words)\n"
        "(6 to 8 words, all naturally usable in a paragraph about the topic, "
        "all appropriate for {level} learners)"
    ),
    LessonFormat.MISTAKE: (
        "- the wrong sentence — the corrected sentence — why it is wrong "
        "(max 12 words, in Vietnamese)\n"
        "(5 mistakes Vietnamese learners really make around this topic at "
        "{level}, each a full short sentence, not a bare phrase)"
    ),
    LessonFormat.UPGRADE: (
        "- the weak or overused phrase — the stronger phrase — when to use it "
        "(max 12 words, in Vietnamese)\n"
        "(5 upgrades a {level} learner can use immediately on this topic, "
        "each pair meaning the same thing at a higher band)"
    ),
}


@dataclass
class AnthropicDrafter:
    api_key: str
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 1200
    _client: Optional[anthropic.Anthropic] = None

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client

    def draft(
        self,
        topic: str,
        level: CEFRLevel,
        lesson_format: LessonFormat = LessonFormat.VOCAB,
        avoid: Sequence[str] = (),
    ) -> Lesson:
        spec = spec_for(lesson_format)
        prompt = DRAFT_PROMPT.format(
            topic=topic,
            level=level,
            avoid_block=(
                AVOID_BLOCK.format(avoid="\n".join(f"- {word}" for word in avoid))
                if avoid
                else ""
            ),
            section=spec.section,
            rows=ROW_INSTRUCTIONS[lesson_format].format(level=level),
            paragraph_block=(
                PARAGRAPH_BLOCK.format(level=level) if spec.needs_paragraph else ""
            ),
        )
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        body = "".join(
            block.text for block in response.content if block.type == "text"
        )
        # The model returns only the sections; the frontmatter is ours to add.
        document = (
            f"---\ntopic: {topic}\nlevel: {level}\nformat: {lesson_format}\n---\n\n"
            f"{body.strip()}\n"
        )
        return markdown_format.parse(document, source="Claude's reply")
